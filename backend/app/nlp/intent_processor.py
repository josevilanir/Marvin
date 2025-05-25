import re
from backend.app.utils.numeros_por_extenso_para_numero import numero_por_extenso_para_numero
import time

class IntentProcessor:
    def __init__(self, main_controller):
        self.controller = main_controller # Para acessar os serviços
        self.intent_patterns = self._define_intent_patterns()

    def _define_intent_patterns(self):
        patterns = [
            # === SystemService Intents ===
            {
                "name": "GET_TIME",
                "regex": re.compile(r"que horas são|horas|me diga as horas|ver horas", re.IGNORECASE),
                "handler": self._handle_get_time,
                "required_service": lambda: self.controller.system_service
            },
            {
                "name": "GET_MARVIN_INFO",
                "regex": re.compile(r"fale sobre você|quem é você|sobre o marvin|me fale mais de você", re.IGNORECASE),
                "handler": self._handle_get_marvin_info,
                "required_service": lambda: self.controller.system_service
            },
            {
                "name": "OPEN_CALCULATOR", # Específico para calculadora
                "regex": re.compile(r"abrir calculadora|calculadora", re.IGNORECASE),
                "handler": self._handle_open_calculator,
                "required_service": lambda: self.controller.system_service
            },
            {
                "name": "OPEN_APP", # Genérico para outros apps
                "regex": re.compile(r"abrir aplicativo\s+(.+)|abra o aplicativo\s+(.+)|abrir\s+(.+)", re.IGNORECASE),
                "entities": {"app_name": [1, 2, 3]},
                "handler": self._handle_open_app,
                "required_service": lambda: self.controller.system_service
            },
            {
                "name": "SEARCH_WEB",
                "regex": re.compile(r"pesquisar na web por\s+(.+)|pesquisar\s+(.+)\s+na web|procure por\s+(.+)|pesquisar por\s+(.+)", re.IGNORECASE),
                "entities": {"query": [1, 2, 3, 4]},
                "handler": self._handle_search_web,
                "required_service": lambda: self.controller.system_service
            },
            {
                "name": "START_TIMER",
                "regex": re.compile(r"defina um timer de\s+(.+)|timer de\s+(.+)|defina timer para\s+(.+)|timer para\s+(.+)", re.IGNORECASE),
                "entities": {"duration": [1, 2, 3, 4]},
                "handler": self._handle_start_timer,
                "required_service": lambda: self.controller.system_service
            },
            {
                "name": "ADJUST_VOLUME",
                "regex": re.compile(r"ajuste o volume para\s+(.+)|volume para\s+(.+)|aumentar volume para\s+(.+)|diminuir volume para\s+(.+)", re.IGNORECASE),
                "entities": {"level": [1, 2, 3, 4]}, # O handler precisará saber se é para aumentar/diminuir se for o caso
                "handler": self._handle_adjust_volume,
                "required_service": lambda: self.controller.system_service
            },

            # === SpotifyService Intents ===
            {
                "name": "PLAY_SPOTIFY_SONG",
                "regex": re.compile(r"tocar (?:música|som|faixa|msc)\s+(.+)|toque (?:música|som|faixa|msc)\s+(.+)", re.IGNORECASE),
                "entities": {"song_name": [1, 2]},
                "handler": self._handle_play_spotify_song,
                "required_service": lambda: self.controller.spotify_service
            },
            {
                "name": "PAUSE_SPOTIFY",
                "regex": re.compile(r"pausar (?:música|spotify|o som)|pause (?:música|spotify|o som)|pausa spotify", re.IGNORECASE),
                "handler": self._handle_pause_spotify,
                "required_service": lambda: self.controller.spotify_service
            },
            {
                "name": "RESUME_SPOTIFY",
                "regex": re.compile(r"play (?:música|spotify|o som)|retomar (?:música|spotify)|continuar (?:música|spotify)", re.IGNORECASE),
                "handler": self._handle_resume_spotify,
                "required_service": lambda: self.controller.spotify_service
            },
            {
                "name": "NEXT_SPOTIFY_TRACK",
                "regex": re.compile(r"próxima (?:música|faixa|som)|avançar (?:música|spotify)", re.IGNORECASE),
                "handler": self._handle_next_spotify_track,
                "required_service": lambda: self.controller.spotify_service
            },
            {
                "name": "PREVIOUS_SPOTIFY_TRACK",
                "regex": re.compile(r"(?:música|faixa|som) anterior|voltar (?:música|spotify)", re.IGNORECASE),
                "handler": self._handle_previous_spotify_track,
                "required_service": lambda: self.controller.spotify_service
            },
            {
                "name": "LIST_SPOTIFY_PLAYLISTS",
                "regex": re.compile(r"listar (?:minhas )?playlists|quais são minhas playlists|minhas playlists", re.IGNORECASE),
                "handler": self._handle_list_spotify_playlists,
                "required_service": lambda: self.controller.spotify_service
            },
            { # Tocar playlist com modo opcional
                "name": "PLAY_SPOTIFY_PLAYLIST",
                "regex": re.compile(r"tocar (?:a )?playlist\s+([^\s]+(?:\s+[^\s]+)*?)(?:\s+no modo\s+(aleatório|padrão))?|toque (?:a )?playlist\s+([^\s]+(?:\s+[^\s]+)*?)(?:\s+no modo\s+(aleatório|padrão))?", re.IGNORECASE),
                "entities": {"playlist_identifier": [1,3], "mode": [2,4]},
                "handler": self._handle_play_spotify_playlist,
                "required_service": lambda: self.controller.spotify_service
            },
            { # Adicionar música à playlist
                "name": "ADD_SPOTIFY_TRACK_TO_PLAYLIST",
                "regex": re.compile(r"adicionar (?:música|som|faixa)\s+(.+?)\s+à playlist\s+(.+)|adicione (?:música|som|faixa)\s+(.+?)\s+na playlist\s+(.+)", re.IGNORECASE),
                "entities": {"song_name": [1,3], "playlist_identifier": [2,4]},
                "handler": self._handle_add_spotify_track_to_playlist,
                "required_service": lambda: self.controller.spotify_service
            },
            { # Listar músicas de uma playlist
                "name": "LIST_SPOTIFY_PLAYLIST_TRACKS",
                "regex": re.compile(r"listar (?:músicas|sons|faixas) da playlist\s+(.+)|o que tem na playlist\s+(.+)|músicas da playlist\s+(.+)", re.IGNORECASE),
                "entities": {"playlist_identifier": [1,2,3]},
                "handler": self._handle_list_spotify_playlist_tracks,
                "required_service": lambda: self.controller.spotify_service
            },
            { # Conectar dispositivo Spotify
                "name": "CONNECT_SPOTIFY_DEVICE",
                "regex": re.compile(r"conectar (?:ao )?dispositivo spotify|conectar spotify ao dispositivo\s+(.+)|listar dispositivos spotify", re.IGNORECASE),
                "entities": {"device_identifier": [1]}, # Se listar, device_identifier será None
                "handler": self._handle_connect_spotify_device,
                "required_service": lambda: self.controller.spotify_service
            },

            # === YouTubeService Intents ===
            { # Tocar/Pesquisar no YouTube
                "name": "SEARCH_PLAY_YOUTUBE",
                "regex": re.compile(r"(?:tocar|pesquisar|buscar|achar|ver)\s+(.+?)\s+no youtube|(?:assistir|youtube)\s+(.+)", re.IGNORECASE),
                "entities": {"query": [1,2], "action_verb_group": 0}, # group 0 is the whole match to check "tocar"
                "handler": self._handle_search_play_youtube,
                "required_service": lambda: self.controller.youtube_service
            },
            { # Clicar vídeo por número/posição
                "name": "CLICK_YOUTUBE_VIDEO_BY_NUMBER",
                "regex": re.compile(r"(?:clicar no|selecionar o|abrir o|tocar o)\s+(?:vídeo número|vídeo na posição|vídeo)\s*([a-zA-Z0-9]+)", re.IGNORECASE),
                "entities": {"position_str": [1]},
                "handler": self._handle_click_youtube_video_by_number,
                "required_service": lambda: self.controller.youtube_service
            },
             { # Selecionar canal (genérico, após pesquisa)
                "name": "SELECT_YOUTUBE_CHANNEL",
                "regex": re.compile(r"(?:ir para o|selecionar o|abrir o)\s+canal(?: do youtube)?", re.IGNORECASE), # Assumes it's the first channel in results
                "handler": self._handle_select_youtube_channel,
                "required_service": lambda: self.controller.youtube_service
            },
            { # Controles de vídeo YouTube
                "name": "CONTROL_YOUTUBE_VIDEO",
                "regex": re.compile(r"(pausar|retomar|continuar|play no|parar o)\s+(?:vídeo|youtube)|(tela cheia|sair da tela cheia|maximizar janela)\s*(?:no youtube)?", re.IGNORECASE),
                "entities": {"control_action_playback": [1], "control_action_window": [2]},
                "handler": self._handle_control_youtube_video,
                "required_service": lambda: self.controller.youtube_service
            },
            { # Pular anúncio YouTube
                "name": "SKIP_YOUTUBE_AD",
                "regex": re.compile(r"pular (?:anúncio|comercial|propaganda)|fechar (?:anúncio|propaganda)", re.IGNORECASE),
                "handler": self._handle_skip_youtube_ad,
                "required_service": lambda: self.controller.youtube_service
            },
            { # Voltar no YouTube
                "name": "GO_BACK_YOUTUBE",
                "regex": re.compile(r"voltar (?:no youtube|página)|página anterior (?:no youtube)", re.IGNORECASE),
                "handler": self._handle_go_back_youtube,
                "required_service": lambda: self.controller.youtube_service
            },

            # === WhatsAppService Intents ===
            {
                "name": "SEND_WHATSAPP_MESSAGE",
                 "regex": re.compile(r"enviar mensagem (?:no whatsapp |whatsapp )?para\s+([^,]+?)(?:,|\s+dizendo|\s+com a mensagem|\s+mensagem)\s+(.+)", re.IGNORECASE),
                "entities": {"contact_name": [1], "message_content": [2]},
                "handler": self._handle_send_whatsapp_message,
                "required_service": lambda: self.controller.whatsapp_service
            },
            
            # === General Intents ===
            {
                "name": "SHUTDOWN",
                "regex": re.compile(r"tchau|adeus|desligar marvin|encerrar marvin", re.IGNORECASE),
                "handler": self._handle_shutdown,
                "required_service": None
            }
            # Adicione mais padrões aqui conforme necessário
        ]
        return patterns

    def process(self, command_text: str) -> str:
        for intent_config in self.intent_patterns:
            match = intent_config["regex"].search(command_text)
            if match:
                print(f"IntentProcessor: Matched intent '{intent_config['name']}' with text '{command_text}'")
                
                service_check = intent_config.get("required_service")
                if service_check:
                    service_instance = service_check()
                    if not service_instance:
                        return f"Desculpe, o serviço para executar '{intent_config['name']}' não está disponível ou não foi inicializado corretamente."
                
                entities = {}
                if "entities" in intent_config:
                    for entity_name, group_indices in intent_config["entities"].items():
                        # Ensure group_indices is always a list/tuple for iteration
                        indices_to_check = group_indices if isinstance(group_indices, (list, tuple)) else [group_indices]
                        for index in indices_to_check:
                            try:
                                if match.group(index):
                                    entities[entity_name] = match.group(index).strip()
                                    print(f"IntentProcessor: Extracted entity '{entity_name}': '{entities[entity_name]}'")
                                    break 
                            except IndexError:
                                # This group index might not exist in this particular regex alternative
                                pass 
                
                # Adicionar o objeto match completo às entidades, pode ser útil em handlers complexos
                entities["_match_obj_"] = match
                return intent_config["handler"](entities, original_command=command_text)
        
        print(f"IntentProcessor: No intent matched for text: '{command_text}'")
        return "Desculpe, não consegui entender o comando."

    # --- Handler Methods (Stubs - Implementar a lógica!) ---

    def _handle_get_time(self, entities, original_command):
        return self.controller.system_service.get_current_datetime_string().get("message")

    def _handle_get_marvin_info(self, entities, original_command):
        return self.controller.system_service.get_marvin_info().get("message")

    def _handle_open_calculator(self, entities, original_command):
        return self.controller.system_service.open_calculator().get("message")

    def _handle_open_app(self, entities, original_command):
        app_name = entities.get("app_name")
        if "calculadora" in (app_name or "").lower() : # Evitar que "abrir calculadora" caia aqui se OPEN_CALCULATOR falhar antes
            return self._handle_open_calculator(entities, original_command)
        if app_name:
            return self.controller.system_service.open_application(app_name).get("message")
        return "Qual aplicativo você gostaria de abrir?"

    def _handle_search_web(self, entities, original_command):
        query = entities.get("query")
        if query:
            return self.controller.system_service.search_web(query).get("message")
        return "O que você gostaria de pesquisar na web?"

    def _handle_start_timer(self, entities, original_command):
        duration = entities.get("duration")
        if duration:
            return self.controller.system_service.start_timer(duration).get("message")
        return "Para quanto tempo devo definir o timer?"

    def _handle_adjust_volume(self, entities, original_command):
        level = entities.get("level")
        if level:
            return self.controller.system_service.adjust_system_volume(level).get("message")
        return "Para qual nível devo ajustar o volume?"

    def _handle_play_spotify_song(self, entities, original_command):
        song_name = entities.get("song_name")
        if song_name:
            return self.controller.spotify_service.play_music(song_name).get("message")
        return "Qual música você gostaria de tocar?"

    def _handle_pause_spotify(self, entities, original_command):
        return self.controller.spotify_service.pause_playback().get("message")

    def _handle_resume_spotify(self, entities, original_command):
        return self.controller.spotify_service.resume_playback().get("message")

    def _handle_next_spotify_track(self, entities, original_command):
        return self.controller.spotify_service.next_track().get("message")

    def _handle_previous_spotify_track(self, entities, original_command):
        return self.controller.spotify_service.previous_track().get("message")

    def _handle_list_spotify_playlists(self, entities, original_command):
        result = self.controller.spotify_service.list_user_playlists()
        if isinstance(result, list) and result: # list_user_playlists returns a list directly
            names = [pl['name'] for pl in result[:5]] 
            return "Suas playlists são: " + ", ".join(names) + ("." if len(names) < len(result) else ", entre outras.")
        elif not result:
             return "Não encontrei nenhuma playlist sua ou não pude acessá-las."
        return result.get("message", "Erro ao listar playlists.")


    def _handle_play_spotify_playlist(self, entities, original_command):
        playlist_identifier = entities.get("playlist_identifier")
        mode = entities.get("mode", "standard") # Default to standard if not captured
        if not playlist_identifier:
             # Try to extract from "tocar playlist NOME_PLAYLIST" if first regex failed
             match = re.search(r"tocar playlist\s+(.+?)(?:\s+no modo\s+(aleatório|padrão))?$", original_command, re.IGNORECASE)
             if match:
                 playlist_identifier = match.group(1).strip()
                 if match.group(2): mode = match.group(2).strip()

        if playlist_identifier:
            return self.controller.spotify_service.play_playlist(playlist_identifier, mode=mode).get("message")
        return "Qual playlist você gostaria de tocar?"

    def _handle_add_spotify_track_to_playlist(self, entities, original_command):
        song_name = entities.get("song_name")
        playlist_identifier = entities.get("playlist_identifier")
        if song_name and playlist_identifier:
            return self.controller.spotify_service.add_track_to_playlist(song_name, playlist_identifier).get("message")
        return "Preciso do nome da música e da playlist para adicionar."

    def _handle_list_spotify_playlist_tracks(self, entities, original_command):
        playlist_identifier = entities.get("playlist_identifier")
        if playlist_identifier:
            result = self.controller.spotify_service.list_tracks_in_playlist(playlist_identifier)
            if result.get("status") == "success":
                tracks = result.get("tracks", [])
                playlist_name = result.get("playlist_name", playlist_identifier)
                if not tracks:
                    return f"A playlist '{playlist_name}' está vazia."
                track_names = [t['name'] for t in tracks[:3]] # List first 3 for voice
                response = f"Na playlist '{playlist_name}' encontrei: " + ", ".join(track_names)
                if len(tracks) > 3:
                    response += f", entre outras {len(tracks) - 3} músicas."
                return response
            return result.get("message", "Não consegui listar as músicas da playlist.")
        return "De qual playlist você gostaria de ver as músicas?"

    def _handle_connect_spotify_device(self, entities, original_command):
        # This is more complex as it involves a dialogue: list, then ask, then connect.
        # For now, let's just list devices. Connecting would need state.
        # The original main.py had "conectar dispositivo" which called listar_e_conectar_dispositivo()
        # which then used reconhece_fala() for subsequent input.
        # This requires more advanced conversation management in MainController.
        # For now, this handler will just list devices.
        # A specific device name from voice could be used if `device_identifier` is captured.
        
        device_identifier_from_command = entities.get("device_identifier")

        devices = self.controller.spotify_service.list_available_devices()
        if not devices:
            return "Nenhum dispositivo Spotify encontrado ou disponível."

        if device_identifier_from_command:
            # Attempt to connect directly if a device name was given
            found_device_id = None
            for device in devices:
                if device_identifier_from_command.lower() in device['name'].lower():
                    found_device_id = device['id']
                    break
            if found_device_id:
                conn_result = self.controller.spotify_service.transfer_playback(found_device_id)
                if conn_result: # transfer_playback returns bool
                    return f"Conectado ao dispositivo {device_identifier_from_command}."
                else:
                    return f"Falha ao conectar ao dispositivo {device_identifier_from_command}."
            else:
                return f"Dispositivo Spotify '{device_identifier_from_command}' não encontrado. Dispositivos disponíveis: " + ", ".join([d['name'] for d in devices])


        # If no specific device name, list them.
        device_names = [d['name'] for d in devices]
        response = "Dispositivos Spotify disponíveis: " + ", ".join(device_names) + ". Qual deles você quer conectar?"
        # The MainController would need to handle the follow-up question.
        # For now, we return this, and the user would need to issue a new "conectar spotify ao dispositivo NOME" command.
        return response


    def _handle_search_play_youtube(self, entities, original_command):
        query = entities.get("query")
        match_obj = entities.get("_match_obj_") # Get the full match object
        action_verb = "pesquisar" # Default
        if match_obj and match_obj.group(0).lower().startswith("tocar"): # Check if first word was "tocar"
            action_verb = "tocar"

        if not query: # Try another common pattern if first regex failed to capture query
            m = re.search(r"(?:youtube|assistir)\s+(.+)", original_command, re.IGNORECASE)
            if m: query = m.group(1).strip()
        
        if query:
            search_result = self.controller.youtube_service.search_youtube(query)
            response = search_result.get("message", "Não consegui pesquisar no YouTube.")
            if search_result.get("status") == "success" and action_verb == "tocar":
                # Automatically click the first video
                time.sleep(0.5) # Brief pause
                click_result = self.controller.youtube_service.click_video_by_position(1)
                response += f" {click_result.get('message')}"
            return response
        return "O que você gostaria de pesquisar ou tocar no YouTube?"

    def _handle_click_youtube_video_by_number(self, entities, original_command):
        position_str = entities.get("position_str")
        if position_str:
            try:
                # Try converting from spoken number first, then direct int
                position = numero_por_extenso_para_numero(position_str)
                if position is None:
                    position = int(position_str)
                
                if position > 0:
                    return self.controller.youtube_service.click_video_by_position(position).get("message")
                else:
                    return "O número do vídeo deve ser positivo."
            except ValueError:
                return f"Número do vídeo inválido: '{position_str}'."
        return "Qual o número do vídeo que deseja selecionar?"

    def _handle_select_youtube_channel(self, entities, original_command):
        # This assumes a search has already been performed and a channel is visible.
        return self.controller.youtube_service.select_channel_from_results().get("message")
        
    def _handle_control_youtube_video(self, entities, original_command):
        playback_action = entities.get("control_action_playback")
        window_action = entities.get("control_action_window")
        action_to_perform = None

        if playback_action:
            pb_action_lower = playback_action.lower()
            if "pausar" in pb_action_lower or "parar" in pb_action_lower:
                action_to_perform = 'toggle_pause_play' # Assuming it's playing
            elif "retomar" in pb_action_lower or "continuar" in pb_action_lower or "play no" in pb_action_lower:
                action_to_perform = 'toggle_pause_play' # Assuming it's paused
        elif window_action:
            wa_action_lower = window_action.lower()
            if "tela cheia" in wa_action_lower:
                action_to_perform = 'fullscreen'
            elif "sair da tela cheia" in wa_action_lower:
                action_to_perform = 'exit_fullscreen'
            elif "maximizar janela" in wa_action_lower:
                action_to_perform = 'maximize_window'
        
        if action_to_perform:
            return self.controller.youtube_service.control_video_playback(action_to_perform).get("message")
        return "Não entendi qual controle de vídeo você quer usar."


    def _handle_skip_youtube_ad(self, entities, original_command):
        result_selenium = self.controller.youtube_service.attempt_skip_ad_selenium()
        if result_selenium.get("status") == "success":
            return result_selenium.get("message")
        # Fallback to PyAutoGUI if Selenium didn't find/click
        time.sleep(0.5) # Give a moment for focus if browser window changed
        result_gui = self.controller.youtube_service.skip_ad_pyautogui()
        # Combine messages or prioritize one
        if result_gui.get("status") == "success":
            return result_gui.get("message")
        return result_selenium.get("message") # Return Selenium's message if GUI also failed or wasn't definitive


    def _handle_go_back_youtube(self, entities, original_command):
        return self.controller.youtube_service.go_back_in_browser_history().get("message")

    def _handle_send_whatsapp_message(self, entities, original_command):
        contact_name = entities.get("contact_name")
        message_content = entities.get("message_content")
        if contact_name and message_content:
            # Optional: Confirmation step
            # response_confirm = self.controller.speech_synthesizer.speak_and_listen(f"Você quer enviar '{message_content}' para {contact_name}?")
            # if "sim" in response_confirm.lower():
            return self.controller.whatsapp_service.send_message(contact_name, message_content).get("message")
            # else:
            # return "Envio da mensagem cancelado."
        return "Para quem e qual mensagem você gostaria de enviar pelo WhatsApp?"

    def _handle_shutdown(self, entities, original_command):
        return "Até logo! Tenha um ótimo dia."