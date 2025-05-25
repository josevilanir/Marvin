# backend/app/voice_interface/speech_synthesizer.py
import os
import pygame
from gtts import gTTS
import tempfile # For safer temporary file creation

class SpeechSynthesizer:
    def __init__(self, lang='pt-br', temp_audio_filename="response.mp3"):
        self.lang = lang
        # Using tempfile for a more robust temporary file path
        self.temp_audio_file = os.path.join(tempfile.gettempdir(), temp_audio_filename)
        
        try:
            pygame.mixer.init()
            print("SpeechSynthesizer: Pygame mixer initialized.")
        except pygame.error as e:
            print(f"SpeechSynthesizer: Failed to initialize Pygame mixer: {e}")
            print("SpeechSynthesizer: Text-to-speech output will not be available.")
            # Fallback or raise error depending on how critical TTS is.
            # For now, methods will check if pygame.mixer is None or not initialized.

    def speak(self, text: str):
        """
        Converts text to speech and plays it.
        Original logic from responde_voz.py.
        """
        if not text:
            print("SpeechSynthesizer: No text provided to speak.")
            return

        if not pygame.mixer.get_init():
            print(f"SpeechSynthesizer: Pygame mixer not initialized. Cannot speak: '{text}'")
            return

        try:
            print(f"SpeechSynthesizer: Synthesizing speech for: '{text}'")
            tts = gTTS(text=text, lang=self.lang, slow=False)
            tts.save(self.temp_audio_file)
            print(f"SpeechSynthesizer: Audio saved to {self.temp_audio_file}")

            pygame.mixer.music.load(self.temp_audio_file)
            pygame.mixer.music.play()

            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10) # Keep CPU usage reasonable

            # Ensure music stops and mixer can release the file
            pygame.mixer.music.stop() 
            # pygame.mixer.music.unload() # Good practice before deleting


        except ConnectionError as ce: # Handle gTTS network issues
            print(f"SpeechSynthesizer: Network error with gTTS: {ce}. Cannot speak.")
        except pygame.error as pe: # Handle Pygame specific errors
            print(f"SpeechSynthesizer: Pygame error during speech playback: {pe}")
        except Exception as e:
            print(f"SpeechSynthesizer: Error during speech synthesis or playback: {e}")
        finally:
            # Clean up the temporary audio file
            # Make sure pygame has released the file. A short delay might sometimes be needed on some OS.
            # pygame.time.wait(100) # Optional small delay
            if os.path.exists(self.temp_audio_file):
                try:
                    os.remove(self.temp_audio_file)
                    print(f"SpeechSynthesizer: Temporary audio file {self.temp_audio_file} removed.")
                except Exception as e:
                    print(f"SpeechSynthesizer: Error removing temporary audio file {self.temp_audio_file}: {e}")
    
    def __del__(self):
        """Ensure pygame mixer is quit when the object is destroyed."""
        if pygame.mixer.get_init():
            pygame.mixer.quit()
            print("SpeechSynthesizer: Pygame mixer quit.")


if __name__ == '__main__':
    try:
        synthesizer = SpeechSynthesizer()
        
        if pygame.mixer.get_init(): # Check if it initialized correctly
            print("\n--- Testing Speech Synthesizer ---")
            synthesizer.speak("Olá! Este é um teste do sintetizador de voz.")
            synthesizer.speak("Testando uma segunda frase para garantir que funciona bem.")
            synthesizer.speak("Marvin está pronto para ajudar.")
        else:
            print("Skipping SpeechSynthesizer test as Pygame mixer failed to initialize.")
            
    except Exception as e:
        print(f"Error in SpeechSynthesizer example: {e}")
        import traceback
        traceback.print_exc()