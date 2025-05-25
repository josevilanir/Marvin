# backend/app/voice_interface/speech_recognizer.py
import speech_recognition as sr
import numpy as np
import noisereduce as nr

class SpeechRecognizer:
    def __init__(self, ambient_duration=1, listen_timeout=5, phrase_time_limit=10):
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.ambient_duration = ambient_duration
        self.listen_timeout = listen_timeout
        self.phrase_time_limit = phrase_time_limit
        
        # Calibrate for ambient noise once upon initialization
        # self._adjust_for_ambient_noise()
        print("SpeechRecognizer: Initialized. Call 'adjust_for_ambient_noise()' before first listen if needed.")

    def _adjust_for_ambient_noise(self):
        """Adjusts the recognizer sensitivity to ambient noise."""
        try:
            with self.microphone as source:
                print("SpeechRecognizer: Calibrating for ambient noise, please be quiet...")
                self.recognizer.adjust_for_ambient_noise(source, duration=self.ambient_duration)
                print("SpeechRecognizer: Calibration complete.")
        except Exception as e:
            print(f"SpeechRecognizer: Error during ambient noise adjustment: {e}")


    def _reduce_noise(self, audio_data: sr.AudioData) -> sr.AudioData | None:
        """
        Reduces noise from the given AudioData object.
        Original logic from reconhece_fala.py.
        """
        try:
            raw_data = audio_data.get_raw_data()
            sample_rate = audio_data.sample_rate
            sample_width = audio_data.sample_width

            # Convert raw data to numpy array
            audio_np = np.frombuffer(raw_data, dtype=np.int16) # Assumes 16-bit audio

            # Reduce noise
            # Note: noisereduce works with floating point arrays, typically in range -1 to 1.
            # If your audio_np is int16, you might need to convert it.
            # However, the original code passed it directly, let's see if it works or needs adjustment.
            # For safety, convert to float and back if issues arise.
            
            # audio_float = audio_np.astype(np.float32) / 32768.0 # Normalize to -1.0 to 1.0 for int16
            # audio_reduzido_float = nr.reduce_noise(y=audio_float, sr=sample_rate)
            # audio_reduzido_np = (audio_reduzido_float * 32768.0).astype(np.int16) # Denormalize

            # Per original code, directly using int16 array (might be fine for noisereduce)
            audio_reduzido_np = nr.reduce_noise(y=audio_np, sr=sample_rate)
            
            reduced_audio_bytes = audio_reduzido_np.tobytes()
            
            return sr.AudioData(reduced_audio_bytes, sample_rate, sample_width)
        except Exception as e:
            print(f"SpeechRecognizer: Error during noise reduction: {e}")
            return audio_data # Return original if reduction fails

    def listen_for_audio_input(self, apply_noise_reduction=True) -> str | None:
        """
        Listens for any audio input, performs STT, and optionally noise reduction.

        Args:
            apply_noise_reduction (bool): Whether to apply noise reduction.

        Returns:
            str | None: The recognized text, or None if an error occurs or no speech is detected.
        """
        # It's good practice to adjust for ambient noise before each distinct listening session
        # if the environment changes, or at least periodically.
        # For simplicity here, we might assume it's done or rely on initial calibration.
        # Consider calling self._adjust_for_ambient_noise() here if needed.
        # self._adjust_for_ambient_noise() # Call this if you want to recalibrate each time

        with self.microphone as source:
            print("SpeechRecognizer: Listening...")
            try:
                # The listen() method now directly handles timeout and phrase_time_limit
                audio = self.recognizer.listen(
                    source,
                    timeout=self.listen_timeout,
                    phrase_time_limit=self.phrase_time_limit
                )

                if apply_noise_reduction:
                    print("SpeechRecognizer: Applying noise reduction...")
                    audio = self._reduce_noise(audio) # audio can be None if _reduce_noise returns None on error
                    if not audio: # If noise reduction failed and returned None
                        print("SpeechRecognizer: Noise reduction failed, skipping STT.")
                        return None


                print("SpeechRecognizer: Recognizing speech...")
                text = self.recognizer.recognize_google(audio, language="pt-BR")
                print(f"SpeechRecognizer: Recognized: '{text}'")
                return text.strip()

            except sr.WaitTimeoutError:
                print("SpeechRecognizer: No speech detected within the timeout period.")
                return None
            except sr.UnknownValueError:
                print("SpeechRecognizer: Could not understand audio.")
                return None
            except sr.RequestError as e:
                print(f"SpeechRecognizer: API request failed; {e}")
                return None
            except Exception as e:
                print(f"SpeechRecognizer: An unexpected error occurred during listening/recognition: {e}")
                return None
    
    # The original 'reconhece_fala' had logic to listen specifically for "Marvin"
    # and extract the command. That logic is better placed in the MainController
    # or a dedicated intent parser that uses listen_for_audio_input().
    # The original 'ouvir_comando_completo' is essentially what listen_for_audio_input() does now.

if __name__ == '__main__':
    try:
        recognizer = SpeechRecognizer(listen_timeout=7, phrase_time_limit=10)
        
        # Important: Calibrate for ambient noise first
        recognizer._adjust_for_ambient_noise() # Manually call for this test

        print("\nSay something in Portuguese (e.g., 'Olá Marvin, que horas são?'):")
        recognized_text = recognizer.listen_for_audio_input()

        if recognized_text:
            print(f"\nMAIN TEST - You said: '{recognized_text}'")
        else:
            print("\nMAIN TEST - No speech was recognized or an error occurred.")

        # Test without noise reduction
        # print("\nSay something again (no noise reduction):")
        # recognized_text_no_nr = recognizer.listen_for_audio_input(apply_noise_reduction=False)
        # if recognized_text_no_nr:
        #     print(f"\nMAIN TEST (No NR) - You said: '{recognized_text_no_nr}'")

    except Exception as e:
        print(f"Error in SpeechRecognizer example: {e}")
        import traceback
        traceback.print_exc()