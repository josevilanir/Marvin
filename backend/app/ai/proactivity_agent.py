# backend/app/ai/proactivity_agent.py
import os
import random
import threading
import time
from typing import Callable

from app.ai.system_observer import SystemObserver

# Processes worth commenting on (lowercase)
_INTERESTING_PROCESSES = {
    "code.exe":        ["Vejo que abriu o VS Code. Trabalhando em algum projeto novo?",
                        "VS Code aberto. Bora codar?"],
    "devenv.exe":      ["Visual Studio aberto. Projeto grande?"],
    "pycharm64.exe":   ["PyCharm rodando. Python hoje?",
                        "Vejo o PyCharm aberto. Algum script novo?"],
    "chrome.exe":      ["Chrome aberto. Pesquisando algo ou só procrastinando?",
                        "Vejo o Chrome aberto. Posso ajudar com alguma pesquisa?"],
    "spotify.exe":     ["Spotify aberto. Boa playlist pra hoje?"],
    "vlc.exe":         ["VLC aberto. Assistindo algo?"],
    "discord.exe":     ["Discord aberto. Dando uma pausa das telas sérias?"],
    "obs64.exe":       ["OBS aberto. Vai gravar algo hoje?",
                        "Vejo o OBS. Live ou gravação?"],
    "blender.exe":     ["Blender aberto! Modelagem 3D hoje?"],
    "figma.exe":       ["Figma aberto. Design em progresso?"],
    "notion.exe":      ["Notion aberto. Organizando as ideias?"],
}

_BREAK_MESSAGES = [
    "Ei, você está na frente do computador há mais de 2 horas. Que tal uma pausa de 5 minutos?",
    "Mais de 2 horas trabalhando sem parar. Levanta, estica as pernas.",
    "Pausa obrigatória: você está aqui há mais de 2h. Descansa um pouco.",
]

_RAM_MESSAGES = [
    "RAM em {ram:.0f}%. Bastante coisa aberta. Quer que eu ajude a ver o que está consumindo?",
    "Memória em {ram:.0f}%. Pode valer fechar algumas abas ou programas.",
    "{ram:.0f}% de RAM usada. Sistema ficando pesado.",
]


class ProactivityAgent:
    """
    Monitors system state and triggers proactive notifications.
    Runs in its own daemon thread. Communicates via callbacks (never touches Qt directly).
    """

    def __init__(
        self,
        observer: SystemObserver,
        notify_callback: Callable[[str], None],
        speak_callback: Callable[[str], None],
        ai_processor=None,          # optional — used to generate richer messages
        check_interval: int = 30,
    ):
        self._observer = observer
        self._notify = notify_callback
        self._speak = speak_callback
        self._ai_processor = ai_processor
        self._interval = check_interval

        self._running = False
        self._thread: threading.Thread | None = None

        # Frequency / state control
        self._last_break_alert: float = 0.0
        self._last_ram_alert: float = 0.0
        self._last_activity_ts: float = time.time()
        self._ram_high_since: float = 0.0
        self._commented_processes: set[str] = set()

        # Cooldown constants (seconds)
        self._BREAK_COOLDOWN = 2 * 60 * 60   # 2 hours
        self._BREAK_THRESHOLD = 2 * 60 * 60  # alert after 2h inactive
        self._RAM_COOLDOWN = 30 * 60          # 30 minutes
        self._RAM_THRESHOLD = 85.0
        self._RAM_SUSTAINED = 60              # seconds RAM must stay high

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(
            target=self._check_loop, daemon=True, name="ProactivityAgent"
        )
        self._thread.start()
        print("ProactivityAgent: started.")

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=self._interval + 2)
        print("ProactivityAgent: stopped.")

    def update_activity(self):
        """Call whenever the user sends a message (resets break timer)."""
        self._last_activity_ts = time.time()

    def set_break_threshold(self, seconds: int):
        """Override break threshold (useful for testing)."""
        self._BREAK_THRESHOLD = seconds

    def set_ram_threshold(self, percent: float):
        """Override RAM threshold (useful for testing)."""
        self._RAM_THRESHOLD = percent

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    def _check_loop(self):
        # Give the system observer a moment to collect first metrics
        time.sleep(self._interval)

        while self._running:
            try:
                state = self._observer.get_state()
                now = time.time()

                self._check_break(now)
                self._check_ram(state, now)
                self._check_process(state)

            except Exception as e:
                print(f"ProactivityAgent: check error: {e}")

            time.sleep(self._interval)

    # ------------------------------------------------------------------
    # Rule 1 — Break alert
    # ------------------------------------------------------------------

    def _check_break(self, now: float):
        inactive_for = now - self._last_activity_ts
        since_last_alert = now - self._last_break_alert

        if inactive_for >= self._BREAK_THRESHOLD and since_last_alert >= self._BREAK_COOLDOWN:
            msg = self._generate_message(
                context="o usuário está na frente do computador há mais de 2 horas sem pausa",
                fallback=random.choice(_BREAK_MESSAGES),
            )
            self._last_break_alert = now
            self._emit(msg)

    # ------------------------------------------------------------------
    # Rule 2 — RAM alert
    # ------------------------------------------------------------------

    def _check_ram(self, state: dict, now: float):
        ram = state.get("ram_percent", 0.0)
        since_last_alert = now - self._last_ram_alert

        if ram >= self._RAM_THRESHOLD:
            if self._ram_high_since == 0.0:
                self._ram_high_since = now  # start tracking
            elif (now - self._ram_high_since) >= self._RAM_SUSTAINED:
                if since_last_alert >= self._RAM_COOLDOWN:
                    template = random.choice(_RAM_MESSAGES)
                    fallback = template.format(ram=ram)
                    msg = self._generate_message(
                        context=f"RAM do sistema está em {ram:.0f}%, alta há mais de 1 minuto",
                        fallback=fallback,
                    )
                    self._last_ram_alert = now
                    self._ram_high_since = 0.0  # reset after alerting
                    self._emit(msg)
        else:
            self._ram_high_since = 0.0  # RAM normalized

    # ------------------------------------------------------------------
    # Rule 3 — Active process comment
    # ------------------------------------------------------------------

    def _check_process(self, state: dict):
        proc = state.get("active_process", "").lower()

        if proc in _INTERESTING_PROCESSES and proc not in self._commented_processes:
            self._commented_processes.add(proc)
            friendly = _INTERESTING_PROCESSES[proc]
            fallback = random.choice(friendly)
            msg = self._generate_message(
                context=f"o usuário acabou de abrir {proc}",
                fallback=fallback,
            )
            self._emit(msg)

    # ------------------------------------------------------------------
    # Message generation
    # ------------------------------------------------------------------

    def _generate_message(self, context: str, fallback: str) -> str:
        """
        Try to generate a natural message via Groq. Falls back to the
        fixed string if AI is unavailable or too slow.
        Runs a fresh Groq call — does NOT affect the main conversation history.
        """
        if self._ai_processor is None:
            return fallback

        try:
            from groq import Groq
            client = Groq(api_key=os.getenv("GROQ_API_KEY", ""))
            resp = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Você é Marvin, assistente de IA pessoal descontraído. "
                            "Responda APENAS com UMA mensagem curta (máx 2 frases), "
                            "sem saudação, sem formatação, com personalidade natural do Marvin."
                        ),
                    },
                    {
                        "role": "user",
                        "content": f"Gere uma notificação proativa para: {context}",
                    },
                ],
                temperature=0.8,
                max_tokens=80,
            )
            text = resp.choices[0].message.content or fallback
            return text.strip()
        except Exception as e:
            print(f"ProactivityAgent: AI message generation failed ({e}), using fallback.")
            return fallback

    # ------------------------------------------------------------------
    # Emit helper — notify + speak
    # ------------------------------------------------------------------

    def _emit(self, message: str):
        print(f"ProactivityAgent: → '{message}'")
        try:
            self._notify(message)
        except Exception as e:
            print(f"ProactivityAgent: notify_callback error: {e}")
        try:
            self._speak(message)
        except Exception as e:
            print(f"ProactivityAgent: speak_callback error: {e}")
