import speech_recognition as sr

def reconhece_fala(lang="pt-BR"):
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Diga algo...")
        audio = recognizer.listen(source)
    
    try:
        texto = recognizer.recognize_google(audio, language=lang)
        print(f"Você disse: {texto}")
        return texto
    except sr.UnknownValueError:
        print("Não consegui entender o que você disse")
        return None
    except sr.RequestError as e:
        print(f"Erro ao se comunicar com o serviço de reconhecimento de fala; {e}")
        return None
