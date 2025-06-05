import speech_recognition as sr
import time
from app.voice_interface.speech_synthesizer import SpeechSynthesizer

synth = SpeechSynthesizer()

class SpeechRecognizer:
    def __init__(self, ambient_duration=1):
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.ambient_duration = ambient_duration

    def calibrate_microphone(self):
        with self.microphone as source:
            print("Ajustando para o ruído ambiente...")
            self.recognizer.adjust_for_ambient_noise(source, duration=self.ambient_duration)
            print("Pronto para ouvir.")

    def listen_for_activation(self, activation_word="marvin"):
        with self.microphone as source:
            print("Escutando...")
            audio = self.recognizer.listen(source, phrase_time_limit=5)
        try:
            command = self.recognizer.recognize_google(audio, language="pt-BR").lower()
            print(f"Usuário disse: {command}")
            if activation_word in command:
                synth.speak("Estou ouvindo")
                return True
        except sr.UnknownValueError:
            pass
        except sr.RequestError as e:
            print(f"Erro ao se comunicar com o serviço de reconhecimento: {e}")
        return False

    def get_command(self):
        with self.microphone as source:
            print("Ouvindo comando...")
            audio = self.recognizer.listen(source, phrase_time_limit=7)
        try:
            command = self.recognizer.recognize_google(audio, language="pt-BR")
            print(f"Comando reconhecido: {command}")
            return command.lower()
        except sr.UnknownValueError:
            print("Não entendi o que foi dito.")
            synth.speak("Desculpe, não entendi o que você disse.")
        except sr.RequestError as e:
            print(f"Erro ao se comunicar com o serviço de reconhecimento: {e}")
            synth.speak("Desculpe, ocorreu um erro ao tentar entender.")
        return ""

    def run(self, callback):
        self.calibrate_microphone()
        while True:
            if self.listen_for_activation():
                command = self.get_command()
                if command:
                    callback(command)
