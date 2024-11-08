import spotipy
from spotipy.oauth2 import SpotifyOAuth
from spotipy.exceptions import SpotifyException
import config
from responde_voz import responde_voz
from utils.spotify_utils import sp


def avancar_musica():
    try:
        sp.next_track()
        responde_voz("Música avançada para a próxima na playlist.")
    except SpotifyException as e:
        responde_voz(f"Erro ao avançar música: {e}")
