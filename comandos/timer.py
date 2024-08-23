import time
import pygame

def tocar_alarme():
    pygame.mixer.init()
    pygame.mixer.music.load("C:/Users/Vilanir/Marvin/utils/despertador.mp3")
    pygame.mixer.music.play()


def definir_timer(tempo):
    # Verificar a unidade de tempo
    if "hora" in tempo or "horas" in tempo:
        segundos = int(tempo.split()[0]) * 3600
    elif "minuto" in tempo or "minutos" in tempo:
        segundos = int(tempo.split()[0]) * 60
    elif "segundo" in tempo or "segundos" in tempo:
        segundos = int(tempo.split()[0])
    else:
        raise ValueError("Unidade de tempo não reconhecida. Use 'segundos', 'minutos' ou 'horas'.")

    # Confirmar o início do timer
    print(f"Timer definido para {tempo}.")
    time.sleep(segundos)
    tocar_alarme()




