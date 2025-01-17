import spotipy
from spotipy.oauth2 import SpotifyOAuth
from spotipy.exceptions import SpotifyException
from utils.spotify_utils import listar_dispositivos_spotify
from utils.numeros_por_extenso_para_numero import numero_por_extenso_para_numero
from responde_voz import responde_voz
from reconhece_fala import reconhece_fala, ouvir_comando_completo
from utils.spotify_utils import sp

def listar_e_conectar_dispositivo():
    dispositivos = listar_dispositivos_spotify()
    if not dispositivos:
        responde_voz("Não há dispositivos disponíveis para conexão.")
        return

    listar_dispositivos(dispositivos)
    escolha = obter_escolha_usuario()
    if not escolha:
        responde_voz("Desculpe, não consegui ouvir o dispositivo que você deseja conectar.")
        return

    dispositivo_id = identificar_dispositivo(escolha, dispositivos)
    if dispositivo_id:
        conectar_dispositivo(dispositivo_id, escolha)
    else:
        responde_voz("Desculpe, não consegui encontrar o dispositivo especificado.")


def listar_dispositivos(dispositivos):
    responde_voz("Dispositivos disponíveis:")
    for i, dispositivo in enumerate(dispositivos):
        print(f"{i+1}. {dispositivo['name']} (ID: {dispositivo['id']})")


def obter_escolha_usuario():
    responde_voz("Qual dispositivo você deseja conectar?")
    return ouvir_comando_completo()


def identificar_dispositivo(escolha, dispositivos):
    try:
        escolha_numero = numero_por_extenso_para_numero(escolha)
        if escolha_numero is not None and 1 <= escolha_numero <= len(dispositivos):
            return dispositivos[escolha_numero - 1]['id']
        return next((d['id'] for d in dispositivos if d['name'].lower() == escolha.lower()), None)
    except ValueError:
        responde_voz("Desculpe, não entendi a seleção do dispositivo.")
        return None


def conectar_dispositivo(dispositivo_id, escolha):
    try:
        sp.transfer_playback(device_id=dispositivo_id, force_play=True)
        responde_voz(f"Conectado ao dispositivo: {escolha}")
    except SpotifyException as e:
        responde_voz(f"Erro ao conectar ao dispositivo: {e}")
