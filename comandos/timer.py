import threading
import time
import pygame

def tocar_alarme():
    pygame.mixer.init()
    pygame.mixer.music.load("C:/Users/Vilanir/Marvin/utils/despertador.mp3")
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        continue

def interpretar_tempo(tempo_str):
    try:
        tempo_str = tempo_str.lower().strip()
        if "hora" in tempo_str:
            return float(tempo_str.split()[0]) * 3600  # Converte horas para segundos
        elif "minuto" in tempo_str:
            return float(tempo_str.split()[0]) * 60  # Converte minutos para segundos
        elif "segundo" in tempo_str:
            return float(tempo_str.split()[0])  # Já está em segundos
        else:
            # Se nenhuma unidade for especificada, assumimos que o valor está em segundos
            return float(tempo_str)
    except ValueError:
        print(f"Erro: '{tempo_str}' não é um valor de tempo válido.")
        return None

def iniciar_timer(duracao_str):
    duracao = interpretar_tempo(duracao_str)
    if duracao is not None:
        print(f"Timer iniciado para {duracao_str}.")
        time.sleep(duracao)  # Aguarda a duração do timer
        print("O tempo acabou!")
        tocar_alarme()

def iniciar_timer_em_thread(duracao_str):
    thread = threading.Thread(target=iniciar_timer, args=(duracao_str,))
    thread.start()
