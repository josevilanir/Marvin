import speech_recognition as sr
import noisereduce as nr
import numpy as np

def reduzir_ruido(audio_data, sample_rate):
    audio_np = np.frombuffer(audio_data, dtype=np.int16)
    audio_reduzido = nr.reduce_noise(y=audio_np, sr=sample_rate)
    return audio_reduzido.tobytes()


def ouvir_palavra_ativacao():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source, duration=1)
        print("Aguardando a palavra de ativação 'Marvin'...")
        while True:
            try:
                audio = recognizer.listen(source, phrase_time_limit=5)
                audio_data = audio.get_raw_data()
                sample_rate = source.SAMPLE_RATE

                # Reduzindo o ruído do áudio
                audio_data_reduzido = reduzir_ruido(audio_data, sample_rate)
                audio_reduzido = sr.AudioData(audio_data_reduzido, sample_rate, audio.sample_width)

                texto = recognizer.recognize_google(audio_reduzido, language="pt-BR")
                if "Marvin" in texto or "marvin" in texto:
                    print("Palavra de ativação 'Marvin' detectada.")
                    return True
            except sr.UnknownValueError:
                continue
            except sr.RequestError as e:
                print(f"Erro ao se comunicar com o serviço de reconhecimento de fala; {e}")
                continue
            except sr.WaitTimeoutError:
                print("Tempo limite de espera excedido.")
                continue

def reconhece_fala(lang="pt-BR"):
    recognizer = sr.Recognizer()

    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source, duration=1)
        
        print("Diga algo...")
        try:
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=5)
        except sr.WaitTimeoutError:
            print("Tempo de escuta esgotado, tente novamente.")
            return None

    try:
        # Reduzindo ruído do áudio capturado
        audio_data = reduzir_ruido(audio.get_raw_data(), source.SAMPLE_RATE)

        # Converte de volta para o formato do Recognizer
        audio = sr.AudioData(audio_data, source.SAMPLE_RATE, source.SAMPLE_WIDTH)

        texto = recognizer.recognize_google(audio, language=lang)
        print(f"Você disse: {texto}")
        return texto
    except sr.UnknownValueError:
        print("Não consegui entender o que você disse")
        return None
    except sr.RequestError as e:
        print(f"Erro ao se comunicar com o serviço de reconhecimento de fala: {e}")
        return None
