import time
from comandos.data_e_hora import obter_data_e_hora
from comandos.sobre_mim import sobre_mim
from comandos.abrir_navegador import abrir_navegador_com_pesquisa
from comandos.abrir_calculadora import abrir_calculadora
from comandos.conectar_dispositivo import listar_e_conectar_dispositivo
from comandos.tocar_musica import tocar_musica, pausar_musica, retomar_musica, adicionar_musica_playlist, listar_playlists, tocar_playlist, listar_musicas_da_playlist, sp
from comandos.proxima_musica import avancar_musica
from comandos.voltar_musica import voltar_musica
from comandos.abrir_aplicativo import abrir_aplicativo
from comandos.enviar_zap import enviar_mensagem_whatsapp
from utils.numeros_por_extenso_para_numero import numero_por_extenso_para_numero
from utils.contato_para_numero import obter_numero_contato
from responde_voz import responde_voz
from reconhece_fala import reconhece_fala

if __name__ == "__main__":
    while True:
        comando = reconhece_fala()
        if comando:
            if "Marvin" in comando:
                responde_voz("Pois não, como posso ajudar você hoje?")
            
            
            elif "tchau" in comando:
                responde_voz("Tchau! Tenha um bom dia!")
                break
            
            
            elif "Que horas são" in comando:
                data_e_hora = obter_data_e_hora()
                responde_voz(data_e_hora)
            
            
            elif "me fale mais de você" in comando:
                sobre = sobre_mim()
                responde_voz(sobre)
            
            
            elif "Abrir navegador" in comando:
                responde_voz("O que você gostaria de pesquisar?")
                pesquisa = reconhece_fala()
                if pesquisa:
                    abrir_navegador_com_pesquisa(pesquisa)
                else:
                    responde_voz("Desculpe, não consegui ouvir o que você deseja pesquisar.")
            
            
            elif "Abrir calculadora" in comando:
                abrir_calculadora()
                responde_voz("Abrindo a calculadora.")
            
            
            elif "tocar música" in comando:
                responde_voz("Qual música você gostaria de ouvir no Spotify?")
                pesquisa = reconhece_fala()
                if pesquisa:
                    tocar_musica(pesquisa)
                else:
                    responde_voz("Desculpe, não consegui ouvir o que você deseja ouvir.")
            
            
            elif "pausar" in comando:
                try:
                    pausar_musica()
                    responde_voz("Reprodução pausada.")
                except Exception as e:
                    responde_voz(str(e))
            
            
            elif "Play" in comando:
                try:
                    retomar_musica()
                except Exception as e:
                    responde_voz(str(e))
            
            
            elif "adicionar música" in comando:
                playlists = listar_playlists()
                responde_voz("Qual música você gostaria de adicionar à playlist?")
                musica = reconhece_fala()
                if musica:
                    responde_voz("Qual playlist você deseja adicionar a música?")
                    escolha_playlist = reconhece_fala()
                    if escolha_playlist:
                        escolha_numero = numero_por_extenso_para_numero(escolha_playlist)
                        if isinstance(escolha_numero, int) and 1 <= escolha_numero <= len(playlists):
                            playlist_id = playlists[escolha_numero - 1]['id']
                        else:
                            playlist_id = next((pl['id'] for pl in playlists if pl['name'].lower() == escolha_playlist.lower()), None)
                        
                        if playlist_id:
                            # Encontrar a URI da música
                            resultados = sp.search(q=musica, type='track', limit=1)
                            if resultados['tracks']['items']:
                                track_uri = resultados['tracks']['items'][0]['uri']
                                adicionar_musica_playlist(playlist_id, track_uri)
                                responde_voz(f"Música '{musica}' adicionada à playlist.")
                            else:
                                responde_voz("Desculpe, não consegui encontrar a música especificada.")
                        else:
                            responde_voz("Desculpe, não consegui encontrar a playlist especificada.")
                    else:
                        responde_voz("Desculpe, não consegui ouvir a playlist que você deseja.")
                else:
                    responde_voz("Desculpe, não consegui ouvir a música que você deseja adicionar.")
            
            
            elif "listar playlists" in comando:
                playlists = listar_playlists()
                if playlists:
                    for i, playlist in enumerate(playlists):
                        print(f"{i+1}. {playlist['name']} (ID: {playlist['id']})")
            
            
            elif "tocar playlist" in comando:
                responde_voz("Qual playlist você deseja ouvir?")
                pesquisa = reconhece_fala()
                if pesquisa:
                # Pergunta pelo modo de reprodução
                    responde_voz("Você deseja ouvir no modo padrão ou aleatório?")
                    modo = reconhece_fala()
        
                    if modo and modo.lower() == 'aleatório':
                        modo = 'shuffle'
                    else:
                        modo = 'standard'
        
                    try:
            # Tenta converter a pesquisa para um número inteiro
                        pesquisa = int(pesquisa)
                    except ValueError:
            # Se não for possível converter, mantém a pesquisa como string
                        pass
        
                    tocar_playlist(pesquisa, modo)
            
            elif "conectar dispositivo" in comando:
                listar_e_conectar_dispositivo()
            
            elif "avançar música" in comando or "próxima música" in comando:
                avancar_musica()

            elif "voltar música" in comando or "música anterior" in comando:
                voltar_musica()    

            elif "listar músicas da playlist" in comando:
                responde_voz("Qual playlist você deseja listar?")
                pesquisa = reconhece_fala()
                if pesquisa:
                    try:
                        pesquisa = int(pesquisa)
                    except ValueError:
                        pass
                    listar_musicas_da_playlist(pesquisa)
            
            elif "Abrir aplicativo" in comando:
                responde_voz("Qual aplicativo você gostaria de abrir?")
                aplicativo = reconhece_fala()
                if aplicativo:
                    abrir_aplicativo(aplicativo)
                    responde_voz(f"Abrindo {aplicativo}.")
                else:
                    responde_voz("Desculpe, não consegui ouvir o nome do aplicativo.")

            elif "Enviar mensagem" in comando:
                responde_voz("Para quem você deseja enviar a mensagem?")
                contato = reconhece_fala()

                if contato:
                    responde_voz(f"O que você gostaria de dizer para {contato}?")
                    mensagem = reconhece_fala()

                    if mensagem:
                        responde_voz(f"Enviando mensagem para {contato}.")
                        enviar_mensagem_whatsapp(contato, mensagem)
                        responde_voz("Mensagem enviada com sucesso.")
                    else:
                        responde_voz("Não consegui entender a mensagem. Por favor, tente novamente.")
                else:
                    responde_voz("Não consegui entender o nome do contato. Por favor, tente novamente.")

            else:
                responde_voz("Desculpe, não entendi o comando.")