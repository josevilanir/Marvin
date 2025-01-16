import spotipy
from spotipy.oauth2 import SpotifyOAuth
import config
from utils.spotify_utils import listar_dispositivos_spotify
from utils.numeros_por_extenso_para_numero import numero_por_extenso_para_numero
from reconhece_fala import reconhece_fala
from responde_voz import responde_voz

sp = spotipy.Spotify(
    auth_manager=SpotifyOAuth(
        client_id=config.SPOTIPY_CLIENT_ID,
        client_secret=config.SPOTIPY_CLIENT_SECRET,
        redirect_uri=config.SPOTIPY_REDIRECT_URI,
        scope="user-read-playback-state,user-modify-playback-state,playlist-modify-private,playlist-modify-public,playlist-read-private"
        ))


def selecionar_dispositivo(dispositivo_id):
    sp.transfer_playback(dispositivo_id, force_play=True)


def tocar_musica(musica):
    results = sp.search(q=musica, type='track', limit=1)
    if results['tracks']['items']:
        track = results['tracks']['items'][0]
        sp.start_playback(uris=[track['uri']])
        print(f"Tocando {track['name']} de {track['artists'][0]['name']}")
    else:
        print("Desculpe, não consegui encontrar a música especificada.")


def listar_playlists():
    playlists = sp.current_user_playlists()
    return playlists['items']


def listar_musicas_da_playlist(pesquisa):
    try:
        playlists = listar_playlists()

        # Tenta converter a escolha para um número
        numero = numero_por_extenso_para_numero(pesquisa)

        if numero is not None:
            if 1 <= numero <= len(playlists):
                playlist_id = playlists[numero - 1]['id']
            else:
                responde_voz("Número da playlist fora do intervalo.")
                return
        else:
            playlist = next(
                (p for p in playlists if p['name'].lower() == pesquisa.lower()), None)
            if playlist:
                playlist_id = playlist['id']
            else:
                responde_voz("Playlist não encontrada.")
                return

        tracks = sp.playlist_tracks(playlist_id)
        musicas = []

        for item in tracks['items']:
            track = item['track']
            nome_musica = track['name']
            artistas = ', '.join([artist['name']
                                 for artist in track['artists']])
            musicas.append(f"{nome_musica} - {artistas}")

        if musicas:
            responde_voz("Aqui está a lista de músicas da playlist:")
            for musica in musicas:
                print(musica)
        else:
            responde_voz("A playlist está vazia.")

    except spotipy.exceptions.SpotifyException as e:
        responde_voz(f"Erro ao listar músicas da playlist: {e}")


def selecionar_playlist_por_voz(playlists):
    for i, playlist in enumerate(playlists):
        print(f"{i+1}. {playlist['name']} (ID: {playlist['id']})")

    escolha_playlist = reconhece_fala()
    if escolha_playlist:
        try:
            escolha_numero = numero_por_extenso_para_numero(escolha_playlist)
            if escolha_numero is not None:
                playlist_id = playlists[escolha_numero - 1]['id']
            else:
                playlist_id = next(
                    (p['id'] for p in playlists if p['name'].lower() == escolha_playlist.lower()),
                    None)

            return playlist_id
        except ValueError:
            responde_voz("Desculpe, não entendi a seleção da playlist.")
    return None


def adicionar_musica_playlist(playlist_id, track_uri):
    sp.playlist_add_items(playlist_id, [track_uri])


def pausar_musica():
    dispositivos = listar_dispositivos_spotify()

    if not dispositivos:
        raise Exception(
            "Nenhum dispositivo disponível. Por favor, verifique se há dispositivos conectados.")

    try:
        sp.pause_playback()
        print("Reprodução pausada.")
    except spotipy.exceptions.SpotifyException as e:
        print(f"Erro ao pausar a reprodução: {e}")


def retomar_musica():
    dispositivos = listar_dispositivos_spotify()

    if not dispositivos:
        raise Exception(
            "Nenhum dispositivo disponível. Por favor, verifique se há dispositivos conectados.")

    try:
        sp.start_playback()
        print("Reprodução retomada.")
    except spotipy.exceptions.SpotifyException as e:
        print(f"Erro ao retomar a reprodução: {e}")


def verificar_dispositivo_ativo():
    dispositivos = sp.devices()
    return dispositivos['devices']


def tocar_playlist(pesquisa, modo='standard'):
    dispositivos = listar_dispositivos_spotify()

    if not dispositivos:
        responde_voz(
            "Nenhum dispositivo disponível. Por favor, verifique se há dispositivos conectados.")
        return

    # Verifica se há um dispositivo ativo
    playback_info = sp.current_playback()
    if not playback_info or not playback_info.get('device'):
        responde_voz(
            "Nenhum dispositivo ativo encontrado. Por favor, selecione um dispositivo.")
        return

    try:
        playlists = listar_playlists()

        # Tenta converter a escolha para um número inteiro
        if isinstance(pesquisa, int):
            numero = pesquisa
        else:
            numero = numero_por_extenso_para_numero(pesquisa)

        if numero is not None:
            # Se a pesquisa for um número, busca a playlist correspondente
            if 1 <= numero <= len(playlists):
                playlist_id = playlists[numero - 1]['id']
            else:
                responde_voz("Número da playlist fora do intervalo.")
                return
        else:
            # Se não for um número, assume que é o nome da playlist
            playlist = next(
                (p for p in playlists if p['name'].lower() == pesquisa.lower()), None)
            if playlist:
                playlist_id = playlist['id']
            else:
                responde_voz("Playlist não encontrada.")
                return


        # Configura o modo de reprodução
        if modo == 'shuffle':
            sp.shuffle(True)
        else:
            sp.shuffle(False)

        # Inicia a reprodução
        sp.start_playback(context_uri=f"spotify:playlist:{playlist_id}")

        responde_voz(f"Reprodução da playlist iniciada no modo {modo}.")
    except spotipy.exceptions.SpotifyException as e:
        responde_voz(f"Erro ao tocar a playlist: {e}")


def tocar_musica_na_playlist(pesquisa_playlist, musica_nome):
    try:
        playlists = listar_playlists()

        # Tenta converter a escolha da playlist para número
        numero_playlist = numero_por_extenso_para_numero(pesquisa_playlist)

        if numero_playlist is not None:
            # Se for um número, seleciona a playlist pela posição na lista
            if 1 <= numero_playlist <= len(playlists):
                playlist = playlists[numero_playlist - 1]
            else:
                responde_voz("Número da playlist fora do intervalo.")
                return
        else:
            # Se não for um número, tenta encontrar a playlist pelo nome
            playlist = next(
                (p for p in playlists if p['name'].lower() == pesquisa_playlist.lower()), None)
            if not playlist:
                responde_voz("Playlist não encontrada.")
                return

        playlist_id = playlist['id']
        playlist_uri = playlist['uri']  # Pega o URI da playlist

        # Recupera todas as músicas da playlist
        tracks = sp.playlist_tracks(playlist_id)
        track_uris = []
        posicao_musica = None

        # Procura a música dentro da playlist e obtém sua posição
        for index, item in enumerate(tracks['items']):
            track = item['track']
            nome_musica = track['name']
            track_uris.append(track['uri'])

            if musica_nome.lower() in nome_musica.lower():
                posicao_musica = index

        if posicao_musica is None:
            responde_voz("Música não encontrada na playlist.")
            return

        # Toca a playlist a partir da música especificada
        sp.start_playback(
            context_uri=playlist_uri, offset={
                "position": posicao_musica})
        responde_voz(f"Tocando {musica_nome} da playlist {playlist['name']}.")

    except spotipy.exceptions.SpotifyException as e:
        responde_voz(f"Erro ao tentar tocar música na playlist: {e}")
