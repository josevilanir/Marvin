import spotipy
from spotipy.oauth2 import SpotifyOAuth
from spotipy.exceptions import SpotifyException
import config
from responde_voz import responde_voz
from utils.spotify_utils import sp


def voltar_musica():
    try:
        sp.previous_track()
        responde_voz("Música retornada para a anterior na playlist.")
    except SpotifyException as e:
        responde_voz(f"Erro ao voltar música: {e}")
