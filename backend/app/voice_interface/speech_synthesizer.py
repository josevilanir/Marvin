# backend/app/voice_interface/speech_synthesizer.py
import io
import os
import threading

import pygame
from dotenv import load_dotenv
from elevenlabs import ElevenLabs

# JARVIS voice from ElevenLabs library
VOICE_ID = "JBFqnCBsd6RMkjVDRZzb"  # George - Warm, Captivating Storyteller (british)
MODEL_ID  = "eleven_multilingual_v2"  # supports Portuguese


class SpeechSynthesizer:
    """
    Text-to-speech via ElevenLabs API (JARVIS - Robot voice).
    Falls back to Edge TTS (pt-BR-AntonioNeural) if API key is missing.
    """

    def __init__(self, rate: int = 175, volume: float = 1.0, voice_lang: str = "pt"):
        self._volume = volume
        self._lock   = threading.Lock()

        load_dotenv()
        api_key = os.getenv("ELEVENLABS_API_KEY")

        if api_key:
            self._client = ElevenLabs(api_key=api_key)
            self._mode   = "elevenlabs"
            print(f"SpeechSynthesizer: ElevenLabs OK (voice {VOICE_ID}).")
        else:
            self._client = None
            self._mode   = "edge"
            print("SpeechSynthesizer: no ELEVENLABS_API_KEY, falling back to Edge TTS.")

        try:
            pygame.mixer.init()
            print("SpeechSynthesizer: pygame mixer OK.")
        except Exception as e:
            print(f"SpeechSynthesizer: pygame mixer init failed ({e}).")

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
                    if self._mode == "elevenlabs":
                        self._speak_elevenlabs(text)
                    else:
                        self._speak_edge(text)
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
        pass  # ElevenLabs doesn't expose rate directly

    def set_volume(self, volume: float):
        self._volume = max(0.0, min(1.0, volume))

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _speak_elevenlabs(self, text: str):
        preview = text[:60] + "…" if len(text) > 60 else text
        print(f"SpeechSynthesizer: speaking → '{preview}'")

        audio_bytes = self._client.text_to_speech.convert(
            voice_id=VOICE_ID,
            text=text,
            model_id=MODEL_ID,
            output_format="mp3_44100_128",
        )

        buf = io.BytesIO(b"".join(audio_bytes))
        buf.seek(0)

        sound = pygame.mixer.Sound(buf)
        sound.set_volume(self._volume)
        channel = sound.play()
        while channel.get_busy():
            import time; time.sleep(0.05)

    def _speak_edge(self, text: str):
        import asyncio
        import edge_tts

        preview = text[:60] + "…" if len(text) > 60 else text
        print(f"SpeechSynthesizer: [edge] speaking → '{preview}'")

        async def _synthesize():
            communicate = edge_tts.Communicate(text, "pt-BR-AntonioNeural")
            buf = io.BytesIO()
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    buf.write(chunk["data"])
            buf.seek(0)
            return buf

        buf = asyncio.run(_synthesize())
        if buf.getbuffer().nbytes == 0:
            return

        sound = pygame.mixer.Sound(buf)
        sound.set_volume(self._volume)
        channel = sound.play()
        import time
        while channel.get_busy():
            time.sleep(0.05)


if __name__ == "__main__":
    synth = SpeechSynthesizer()
    synth.speak("Olá! Todos os sistemas operacionais. Como posso ajudá-lo?")
