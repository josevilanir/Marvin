import spotipy
from spotipy.oauth2 import SpotifyOAuth
import config

# Autenticação com Spotify
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=config.SPOTIPY_CLIENT_ID,
    client_secret=config.SPOTIPY_CLIENT_SECRET,
    redirect_uri=config.SPOTIPY_REDIRECT_URI,
    scope="user-read-playback-state,user-modify-playback-state"
))


def listar_dispositivos_spotify():
    devices = sp.devices()
    return devices['devices'] if devices else []
