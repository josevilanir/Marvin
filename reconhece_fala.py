import speech_recognition as sr
import numpy as np
import noisereduce as nr

def reduzir_ruido(audio_data, sample_rate):
    audio_np = np.frombuffer(audio_data, dtype=np.int16)
    audio_reduzido = nr.reduce_noise(y=audio_np, sr=sample_rate)
    return audio_reduzido.tobytes()

def reconhece_fala():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source, duration=1)
        print("Marvin está ouvindo...")

        while True:
            try:
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
                audio_data = audio.get_raw_data()
                sample_rate = source.SAMPLE_RATE

                # Reduzindo o ruído do áudio
                audio_data_reduzido = reduzir_ruido(audio_data, sample_rate)
                audio_reduzido = sr.AudioData(audio_data_reduzido, sample_rate, audio.sample_width)

                # Reconhecendo o texto
                texto = recognizer.recognize_google(audio_reduzido, language="pt-BR")
                print(f"Você disse: {texto}")

                if "Marvin" in texto or "marvin" in texto:
                    # Extraindo o comando a partir da palavra "Marvin"
                    comando = texto.split("Marvin", 1)[1].strip()
                    print(f"Executando comando: {comando}")
                    return comando

            except sr.UnknownValueError:
                print("Não consegui entender o que você disse.")
                continue
            except sr.RequestError as e:
                print(f"Erro ao se comunicar com o serviço de reconhecimento de fala; {e}")
                continue
            except sr.WaitTimeoutError:
                print("Tempo de escuta esgotado, tente novamente.")
                continue

def ouvir_comando_completo():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source, duration=1)
        print("Marvin está ouvindo...")

        while True:
            try:
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=5)
                audio_data = audio.get_raw_data()
                sample_rate = source.SAMPLE_RATE

                # Reduzindo o ruído do áudio
                audio_data_reduzido = reduzir_ruido(audio_data, sample_rate)
                audio_reduzido = sr.AudioData(audio_data_reduzido, sample_rate, audio.sample_width)

                # Reconhecendo o texto
                texto = recognizer.recognize_google(audio_reduzido, language="pt-BR")
                print(f"Você disse: {texto}")
                
                # Mantendo a frase completa com "Marvin"
                comando = texto.strip()
                print(f"Executando comando completo: {comando}")
                return comando
            except sr.UnknownValueError:
                print("Não consegui entender o que você disse.")
                continue
            except sr.RequestError as e:
                print(f"Erro ao se comunicar com o serviço de reconhecimento de fala; {e}")
                continue
            except sr.WaitTimeoutError:
                print("Tempo de escuta esgotado, tente novamente.")
                continue

            