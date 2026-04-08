import speech_recognition as sr
import time

class SpeechRecognizer:
    def __init__(self, ambient_duration=1):
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.ambient_duration = ambient_duration

    def adjust_for_ambient_noise(self, duration=1):
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=duration)

    def calibrate_microphone(self):
        with self.microphone as source:
            print("Ajustando para o ruído ambiente...")
            self.recognizer.adjust_for_ambient_noise(source, duration=self.ambient_duration)
            print("Pronto para ouvir.")

    def listen_for_activation(self, activation_words=None):
        if activation_words is None:
            activation_words = ["marvin", "marv", "marvi", "mar"]

        with self.microphone as source:
            print("Escutando...")
            audio = self.recognizer.listen(source, phrase_time_limit=40)

        try:
            command = self.recognizer.recognize_google(audio, language="pt-BR").lower()
            print(f"Usuário disse: {command}")

            if any(word in command for word in activation_words):
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
            audio = self.recognizer.listen(source, phrase_time_limit=40)
        try:
            command = self.recognizer.recognize_google(audio, language="pt-BR")
            print(f"Comando reconhecido: {command}")
            return command.lower()
        except sr.UnknownValueError:
            print("Não entendi o que foi dito.")
        except sr.RequestError as e:
            print(f"Erro ao se comunicar com o serviço de reconhecimento: {e}")
        return ""

    def run(self, callback):
        self.calibrate_microphone()
        while True:
            if self.listen_for_activation():
                command = self.get_command()
                if command:
                    callback(command)

    def recognize_once(self, timeout=8, phrase_time_limit=15):
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source)
            print("SpeechRecognizer: Aguardando fala...")
            try:
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
            except sr.WaitTimeoutError:
                print("SpeechRecognizer: Tempo esgotado sem detectar fala.")
                return ""

        try:
            texto = self.recognizer.recognize_google(audio, language='pt-BR')
            print(f"SpeechRecognizer: Você disse: {texto}")
            return texto
        except sr.UnknownValueError:
            print("SpeechRecognizer: Não entendi o que foi dito.")
            return ""
        except sr.RequestError as e:
            print(f"SpeechRecognizer: Erro na requisição: {e}")
            raise
