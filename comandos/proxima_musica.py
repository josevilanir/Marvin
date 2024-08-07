import spotipy
from spotipy.oauth2 import SpotifyOAuth
from spotipy.exceptions import SpotifyException
import config
from responde_voz import responde_voz

# Autenticação com Spotify
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=config.SPOTIPY_CLIENT_ID,
    client_secret=config.SPOTIPY_CLIENT_SECRET,
    redirect_uri=config.SPOTIPY_REDIRECT_URI,
    scope="user-read-playback-state,user-modify-playback-state"
))

def avancar_musica():
    try:
        sp.next_track()
        responde_voz("Música avançada para a próxima na playlist.")
    except SpotifyException as e:
        responde_voz(f"Erro ao avançar música: {e}")
