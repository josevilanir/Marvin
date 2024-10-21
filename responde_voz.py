import os
import time
import pygame
from gtts import gTTS


def responde_voz(texto):
    diretório_atual = os.path.dirname(os.path.abspath(__file__))
    caminho_arquivo = os.path.join(diretório_atual, "resposta.mp3")
    tts = gTTS(texto, lang='pt')
    tts.save(caminho_arquivo)
    pygame.mixer.init()
    pygame.mixer.music.load(caminho_arquivo)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(1)
    pygame.mixer.quit()
    os.remove(caminho_arquivo)
