# backend/app/voice_interface/speech_synthesizer.py
import sys
import threading


class SpeechSynthesizer:
    """
    Local text-to-speech via pyttsx3.

    pyttsx3's runAndWait() conflicts with QThread's event loop on Windows,
    causing a permanent hang. Fix: always run speech in a plain threading.Thread,
    which works regardless of the caller's thread type.
    """

    def __init__(self, rate: int = 175, volume: float = 1.0, voice_lang: str = "pt"):
        self._rate       = rate
        self._volume     = volume
        self._voice_lang = voice_lang
        self._lock       = threading.Lock()   # prevents overlapping speech

        # Probe pyttsx3 on the main thread to validate it works + pick voice id
        self._voice_id = None
        try:
            import pyttsx3
            engine = pyttsx3.init()
            self._voice_id = self._find_voice(engine, voice_lang)
            engine.stop()
            print("SpeechSynthesizer: pyttsx3 OK.")
        except Exception as e:
            print(f"SpeechSynthesizer: pyttsx3 probe failed ({e}).")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def speak(self, text: str):
        """Speak text synchronously (blocks caller until done)."""
        if not text:
            return
        with self._lock:
            done  = threading.Event()
            error = [None]

            def _run():
                try:
                    self._speak_in_thread(text)
                except Exception as e:
                    error[0] = e
                finally:
                    done.set()

            t = threading.Thread(target=_run, daemon=True)
            t.start()
            done.wait()

            if error[0]:
                print(f"SpeechSynthesizer: speak error — {error[0]}")

    def set_rate(self, rate: int):
        self._rate = rate

    def set_volume(self, volume: float):
        self._volume = max(0.0, min(1.0, volume))

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _speak_in_thread(self, text: str):
        """
        Creates a fresh pyttsx3 engine per call inside a plain threading.Thread.
        A plain thread avoids the QThread/COM message-loop conflict.
        """
        try:
            import pythoncom
            pythoncom.CoInitialize()
        except ImportError:
            pass

        try:
            import pyttsx3
            engine = pyttsx3.init()
            engine.setProperty("rate",   self._rate)
            engine.setProperty("volume", self._volume)
            if self._voice_id:
                engine.setProperty("voice", self._voice_id)
            preview = text[:60] + "…" if len(text) > 60 else text
            print(f"SpeechSynthesizer: speaking → '{preview}'")
            engine.say(text)
            engine.runAndWait()
        except Exception as e:
            print(f"SpeechSynthesizer: error in thread — {e}")
            raise

    @staticmethod
    def _find_voice(engine, lang_hint: str) -> str | None:
        voices = engine.getProperty("voices")
        for v in voices:
            if lang_hint.lower() in v.id.lower() or lang_hint.lower() in v.name.lower():
                print(f"SpeechSynthesizer: voice → '{v.name}'")
                return v.id
        if voices:
            print(f"SpeechSynthesizer: no '{lang_hint}' voice, using default '{voices[0].name}'")
            return voices[0].id
        return None


if __name__ == "__main__":
    synth = SpeechSynthesizer()
    synth.speak("Olá! Sou o Marvin. Fala aí, o que você precisa?")
    synth.speak("Sistema de voz local pronto.")
