# backend/app/voice_interface/speech_synthesizer.py
import pyttsx3
import threading


class SpeechSynthesizer:
    """
    Local text-to-speech via pyttsx3.
    Zero network latency, no temp files, no pygame dependency.
    """

    def __init__(self, rate: int = 175, volume: float = 1.0, voice_lang: str = "pt"):
        """
        Args:
            rate:       Words per minute (default 175 — natural conversational pace).
            volume:     0.0 – 1.0 (default 1.0).
            voice_lang: Preferred language substring for voice selection (e.g. 'pt', 'en').
        """
        self._lock = threading.Lock()
        try:
            self._engine = pyttsx3.init()
            self._engine.setProperty("rate", rate)
            self._engine.setProperty("volume", volume)
            self._set_voice(voice_lang)
            print("SpeechSynthesizer: pyttsx3 initialized.")
        except Exception as e:
            print(f"SpeechSynthesizer: Failed to initialize pyttsx3: {e}")
            self._engine = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def speak(self, text: str):
        """Synthesize and play text synchronously (blocks until done)."""
        if not text:
            return
        if not self._engine:
            print(f"SpeechSynthesizer: engine not available. Would say: '{text}'")
            return

        with self._lock:
            try:
                print(f"SpeechSynthesizer: speaking → '{text}'")
                self._engine.say(text)
                self._engine.runAndWait()
            except RuntimeError as e:
                # runAndWait can raise if called while already running (edge case)
                print(f"SpeechSynthesizer: RuntimeError during speak: {e}")
            except Exception as e:
                print(f"SpeechSynthesizer: Error during speak: {e}")

    def set_rate(self, rate: int):
        if self._engine:
            self._engine.setProperty("rate", rate)

    def set_volume(self, volume: float):
        if self._engine:
            self._engine.setProperty("volume", max(0.0, min(1.0, volume)))

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _set_voice(self, lang_hint: str):
        """Pick the first available voice whose id or name contains lang_hint."""
        if not self._engine:
            return
        voices = self._engine.getProperty("voices")
        for voice in voices:
            if lang_hint.lower() in voice.id.lower() or lang_hint.lower() in voice.name.lower():
                self._engine.setProperty("voice", voice.id)
                print(f"SpeechSynthesizer: using voice '{voice.name}'")
                return
        # Fallback: keep default voice
        if voices:
            print(f"SpeechSynthesizer: no '{lang_hint}' voice found, using default '{voices[0].name}'")


if __name__ == "__main__":
    synth = SpeechSynthesizer()
    synth.speak("Olá! Sou o Marvin. Fala aí, o que você precisa?")
    synth.speak("Sistema de voz local pronto. Sem internet necessária.")
