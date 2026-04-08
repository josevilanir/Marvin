# frontend/bridge.py
import os
import sys

from PyQt6.QtCore import QObject, QThread, pyqtSignal, pyqtSlot

# Ensure backend is importable
_backend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend")
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))


class _AIWorker(QObject):
    """
    All heavy initialization happens in setup(), which runs inside the QThread.
    __init__ is intentionally minimal so MarvinBridge() returns instantly.
    """

    response_ready       = pyqtSignal(str)
    speaking_start       = pyqtSignal()
    speaking_end         = pyqtSignal()
    status_changed       = pyqtSignal(str)
    proactive_notify     = pyqtSignal(str)
    ready                = pyqtSignal()        # emitted when setup() finishes

    _proactive_speak_req = pyqtSignal(str)     # internal: queued to this thread

    def __init__(self):
        super().__init__()
        # Only wire the internal signal — no heavy work here
        self._proactive_speak_req.connect(self._on_proactive_speak)

        self._processor = None
        self._synth     = None
        self._observer  = None
        self._agent     = None
        self._tool_registry = None

    # ------------------------------------------------------------------
    # Called once when QThread starts (runs in worker thread)
    # ------------------------------------------------------------------

    @pyqtSlot()
    def setup(self):
        """
        Heavy initialization — runs in the worker thread.
        AI core (processor + TTS) sobe primeiro para o chat funcionar imediatamente.
        Serviços externos (Spotify, YouTube...) são registrados em daemon thread
        separada para não bloquear o event loop caso precisem de OAuth.
        """
        import threading
        from app.ai.tool_registry import ToolRegistry
        from app.ai.ai_processor import AIProcessor
        from app.ai.conversation_manager import ConversationManager
        from app.ai.jarvis_personality import SYSTEM_PROMPT
        from app.ai.service_registrar import register_all
        from app.ai.system_observer import SystemObserver
        from app.ai.proactivity_agent import ProactivityAgent
        from app.voice_interface.speech_synthesizer import SpeechSynthesizer

        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            print("Bridge: GROQ_API_KEY não encontrado no .env")
            self.status_changed.emit("erro: sem API key")
            return

        # ── 1. Core AI — sobe rápido, event loop permanece livre ────────
        self._tool_registry = ToolRegistry()

        conversation = ConversationManager()
        self._processor = AIProcessor(
            api_key=api_key,
            tool_registry=self._tool_registry,
            conversation_manager=conversation,
            system_prompt=SYSTEM_PROMPT,
        )
        self._synth = SpeechSynthesizer(voice_lang="pt")

        # ── 2. Serviços externos — daemon thread para não bloquear ──────
        def _register_bg():
            self._register_services(self._tool_registry, register_all)
            print("Bridge: serviços externos registrados.")

        threading.Thread(target=_register_bg, daemon=True, name="ServiceRegistrar").start()

        # ── 3. Proatividade — não depende dos serviços externos ─────────
        self._observer = SystemObserver(interval_seconds=5)
        self._agent = ProactivityAgent(
            observer=self._observer,
            notify_callback=self.proactive_notify.emit,
            speak_callback=self._proactive_speak_req.emit,
            ai_processor=self._processor,
            check_interval=30,
        )
        self._observer.start()
        self._agent.start()

        self.status_changed.emit("idle")
        self.ready.emit()   # emite imediatamente — chat já está funcional

    # ------------------------------------------------------------------
    # Slots called from main thread via queued connections
    # ------------------------------------------------------------------

    @pyqtSlot(str)
    def handle_text(self, text: str):
        if not self._processor:
            self.response_ready.emit("Ainda inicializando, aguarde um momento...")
            return

        if self._agent:
            self._agent.update_activity()

        self.status_changed.emit("thinking")
        try:
            reply = self._processor.process(text)
        except Exception as e:
            reply = f"Erro interno: {e}"

        self.response_ready.emit(reply)
        self._speak_with_signals(reply)

    @pyqtSlot(bool)
    def handle_mic(self, active: bool):
        if active:
            self.status_changed.emit("listening")
            self._listen_once()
        else:
            self.status_changed.emit("idle")

    @pyqtSlot(str)
    def _on_proactive_speak(self, text: str):
        self._speak_with_signals(text)

    @pyqtSlot()
    def shutdown(self):
        if self._agent:
            self._agent.stop()
        if self._observer:
            self._observer.stop()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _speak_with_signals(self, text: str):
        if not self._synth:
            return
        self.speaking_start.emit()
        self.status_changed.emit("speaking")
        try:
            self._synth.speak(text)
        finally:
            self.speaking_end.emit()
            self.status_changed.emit("idle")

    def _listen_once(self):
        try:
            from app.voice_interface.speech_recognizer import SpeechRecognizer
            recognizer = SpeechRecognizer()
            # adjust_for_ambient_noise já é chamado dentro de recognize_once
            transcription = recognizer.recognize_once()
            if transcription:
                self.handle_text(transcription)
            else:
                self.response_ready.emit("_(não entendi — tente falar mais perto do microfone)_")
                self.status_changed.emit("idle")
        except Exception as e:
            print(f"Bridge: voice recognition error: {e}")
            self.response_ready.emit(f"_(erro no microfone: {e})_")
            self.status_changed.emit("idle")

    @staticmethod
    def _register_services(registry, register_all_fn):
        try:
            from app.core.config_manager import ConfigManager
            from app.services.system_service import SystemService
            from app.services.spotify_service import SpotifyService
            from app.services.youtube_service import YouTubeService
            from app.services.whatsapp_service import WhatsAppService

            cfg = ConfigManager()
            spotify = youtube = whatsapp = system = None

            # Register SystemService first — fast, no OAuth, needed for core commands
            try:
                system = SystemService(cfg)
            except Exception as e:
                print(f"Bridge: SystemService skipped — {e}")

            # Register system tools immediately so they're available during OAuth waits
            from app.ai.service_registrar import register_system
            if system:
                try:
                    register_system(registry, system)
                    print("Bridge: SystemService registrado antecipadamente.")
                except Exception as e:
                    print(f"Bridge: Falha ao registrar SystemService antecipadamente: {e}")

            try:
                spotify = SpotifyService(cfg)
            except Exception as e:
                print(f"Bridge: SpotifyService skipped — {e}")
            try:
                youtube = YouTubeService(cfg)
            except Exception as e:
                print(f"Bridge: YouTubeService skipped — {e}")
            try:
                whatsapp = WhatsAppService(cfg)
            except Exception as e:
                print(f"Bridge: WhatsAppService skipped — {e}")

            names = register_all_fn(registry, spotify=spotify, youtube=youtube,
                                    whatsapp=whatsapp, system=system)
            print(f"Bridge: {len(names)} ferramentas registradas.")
        except Exception as e:
            print(f"Bridge: Falha ao registrar serviços: {e}")


class MarvinBridge(QObject):
    """
    Public interface between Qt main thread and the AI worker thread.
    Instantiation is instant — all heavy work deferred to setup() in QThread.
    """

    marvin_response       = pyqtSignal(str)
    marvin_speaking_start = pyqtSignal()
    marvin_speaking_end   = pyqtSignal()
    status_changed        = pyqtSignal(str)
    proactive_message     = pyqtSignal(str)

    _text_submitted       = pyqtSignal(str)
    _mic_toggled          = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._thread = QThread()
        self._worker = _AIWorker()
        self._worker.moveToThread(self._thread)

        # Worker → Bridge
        self._worker.response_ready.connect(self.marvin_response)
        self._worker.speaking_start.connect(self.marvin_speaking_start)
        self._worker.speaking_end.connect(self.marvin_speaking_end)
        self._worker.status_changed.connect(self.status_changed)
        self._worker.proactive_notify.connect(self.proactive_message)

        # Bridge → Worker
        self._text_submitted.connect(self._worker.handle_text)
        self._mic_toggled.connect(self._worker.handle_mic)

        # When thread starts → run setup(); when setup finishes → greet
        self._thread.started.connect(self._worker.setup)
        self._worker.ready.connect(self._on_worker_ready)

        # Graceful shutdown
        self._thread.finished.connect(self._worker.shutdown)

    def start(self):
        self._thread.start()   # triggers setup() in worker thread

    def stop(self):
        self._worker.shutdown()
        self._thread.quit()
        self._thread.wait(5000)

    @pyqtSlot()
    def _on_worker_ready(self):
        """Send greeting once the worker has fully initialized."""
        self._text_submitted.emit("Olá! Inicie com uma saudação curta ao usuário.")

    def submit_text(self, text: str):
        self._text_submitted.emit(text)

    def set_mic_active(self, active: bool):
        self._mic_toggled.emit(active)
