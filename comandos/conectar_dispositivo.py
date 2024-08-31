import spotipy
from spotipy.oauth2 import SpotifyOAuth
from spotipy.exceptions import SpotifyException
from utils.spotify_utils import listar_dispositivos_spotify
from utils.numeros_por_extenso_para_numero import numero_por_extenso_para_numero
from responde_voz import responde_voz
from reconhece_fala import reconhece_fala, ouvir_comando_completo
import config

# Autenticação com Spotify
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=config.SPOTIPY_CLIENT_ID,
    client_secret=config.SPOTIPY_CLIENT_SECRET,
    redirect_uri=config.SPOTIPY_REDIRECT_URI,
    scope="user-read-playback-state,user-modify-playback-state"
))

def listar_e_conectar_dispositivo():
    dispositivos = listar_dispositivos_spotify()
    if dispositivos:
        responde_voz("Dispositivos disponíveis:")
        for i, dispositivo in enumerate(dispositivos):
            print(f"{i+1}. {dispositivo['name']} (ID: {dispositivo['id']})")
            

        responde_voz("Qual dispositivo você deseja conectar?")
        escolha = ouvir_comando_completo()
        if escolha:
            try:
                # Tenta converter a escolha para um número
                escolha_numero = numero_por_extenso_para_numero(escolha)
                if escolha_numero is not None and 1 <= escolha_numero <= len(dispositivos):
                    dispositivo_id = dispositivos[escolha_numero - 1]['id']
                else:
                    # Caso não seja um número por extenso ou fora do intervalo, tenta converter a escolha direta
                    dispositivo_id = next((d['id'] for d in dispositivos if d['name'].lower() == escolha.lower()), None)

                if dispositivo_id:
                    try:
                        sp.transfer_playback(device_id=dispositivo_id, force_play=True)
                        responde_voz(f"Conectado ao dispositivo: {escolha}")
                    except SpotifyException as e:
                        responde_voz(f"Erro ao conectar ao dispositivo: {e}")
                else:
                    responde_voz("Desculpe, não consegui encontrar o dispositivo especificado.")
            except ValueError:
                responde_voz("Desculpe, não entendi a seleção do dispositivo.")
        else:
            responde_voz("Desculpe, não consegui ouvir o dispositivo que você deseja conectar.")
    else:
        responde_voz("Não há dispositivos disponíveis para conexão.")
