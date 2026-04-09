# backend/app/ai/service_registrar.py
"""
Registra todos os serviços no ToolRegistry com wrappers finos que alinham
os nomes de parâmetros esperados pelo LLM com as assinaturas reais dos serviços.

Regra: serviços não são modificados — apenas adaptados aqui.
"""
from app.ai.tool_registry import ToolRegistry


def _param(name: str, type_: str, description: str, required: bool = True) -> tuple:
    return name, type_, description, required


def _schema(*params, required: list[str] = None) -> dict:
    """Build a minimal JSON-Schema 'object' from a list of (name, type, desc) tuples."""
    properties = {}
    req = required or []
    for name, type_, desc, is_req in params:
        properties[name] = {"type": type_, "description": desc}
        if is_req:
            req.append(name)
    return {"type": "object", "properties": properties, "required": req}


def _no_params() -> dict:
    return {"type": "object", "properties": {}}


# ─────────────────────────────────────────────────────────────────────────────
# 4.2  SpotifyService
# ─────────────────────────────────────────────────────────────────────────────

def register_spotify(registry: ToolRegistry, spotify):
    """Register SpotifyService tools. `spotify` is a SpotifyService instance."""

    registry.register(
        name="play_music",
        description="Toca uma música, artista ou álbum no Spotify",
        parameters=_schema(
            _param("query", "string", "Nome da música, artista ou álbum a tocar"),
        ),
        handler=lambda query: spotify.play_music(track_name=query),
    )

    registry.register(
        name="pause_music",
        description="Pausa a reprodução atual no Spotify",
        parameters=_no_params(),
        handler=lambda **_: spotify.pause_playback(),
    )

    registry.register(
        name="resume_music",
        description="Retoma a reprodução pausada no Spotify",
        parameters=_no_params(),
        handler=lambda **_: spotify.resume_playback(),
    )

    registry.register(
        name="next_track",
        description="Pula para a próxima faixa no Spotify",
        parameters=_no_params(),
        handler=lambda **_: spotify.next_track(),
    )

    registry.register(
        name="previous_track",
        description="Volta para a faixa anterior no Spotify",
        parameters=_no_params(),
        handler=lambda **_: spotify.previous_track(),
    )

    registry.register(
        name="set_spotify_volume",
        description="Ajusta o volume do Spotify (0 a 100)",
        parameters=_schema(
            _param("volume", "integer", "Nível de volume de 0 a 100"),
        ),
        handler=lambda volume: _spotify_set_volume(spotify, volume),
    )

    registry.register(
        name="get_current_track",
        description="Retorna informações sobre a música que está tocando agora no Spotify",
        parameters=_no_params(),
        handler=lambda **_: _spotify_current_track(spotify),
    )

    registry.register(
        name="play_playlist",
        description="Toca uma playlist do Spotify pelo nome ou número",
        parameters=_schema(
            _param("playlist", "string", "Nome ou número da playlist"),
            _param("mode", "string", "Modo de reprodução: 'standard' ou 'shuffle'", required=False),
        ),
        handler=lambda playlist, mode="standard": spotify.play_playlist(
            playlist_identifier=playlist, mode=mode
        ),
    )


def _spotify_set_volume(spotify, volume: int) -> dict:
    try:
        vol = max(0, min(100, int(volume)))
        spotify.sp.volume(vol)
        return {"status": "success", "message": f"Volume do Spotify ajustado para {vol}%."}
    except Exception as e:
        return {"status": "error", "message": f"Erro ao ajustar volume do Spotify: {e}"}


def _spotify_current_track(spotify) -> dict:
    try:
        playback = spotify.sp.current_playback()
        if not playback or not playback.get("item"):
            return {"status": "info", "message": "Nenhuma música tocando no momento."}
        item = playback["item"]
        name = item["name"]
        artists = ", ".join(a["name"] for a in item.get("artists", []))
        progress_ms = playback.get("progress_ms", 0)
        duration_ms = item.get("duration_ms", 1)
        progress = f"{progress_ms // 60000}:{(progress_ms % 60000) // 1000:02d}"
        duration = f"{duration_ms // 60000}:{(duration_ms % 60000) // 1000:02d}"
        return {
            "status": "success",
            "message": f"Tocando agora: '{name}' de {artists} ({progress}/{duration})",
        }
    except Exception as e:
        return {"status": "error", "message": f"Erro ao obter faixa atual: {e}"}


# ─────────────────────────────────────────────────────────────────────────────
# 4.3  YouTubeService
# ─────────────────────────────────────────────────────────────────────────────

def register_youtube(registry: ToolRegistry, youtube):
    """Register YouTubeService tools."""

    registry.register(
        name="youtube_search",
        description="Abre o YouTube e pesquisa por um termo. Use antes de youtube_play_video.",
        parameters=_schema(
            _param("query", "string", "Termo a pesquisar no YouTube"),
        ),
        handler=lambda query: youtube.search_youtube(query),
    )

    registry.register(
        name="youtube_play_video",
        description="Clica em um vídeo pelo número de posição nos resultados do YouTube (começa em 1)",
        parameters=_schema(
            _param("index", "integer", "Posição do vídeo nos resultados (1 = primeiro)"),
        ),
        handler=lambda index=1: youtube.click_video_by_position(position=int(index)),
    )

    registry.register(
        name="youtube_pause",
        description="Pausa ou retoma o vídeo atual no YouTube",
        parameters=_no_params(),
        handler=lambda **_: youtube.control_video_playback("toggle_pause_play"),
    )

    registry.register(
        name="youtube_fullscreen",
        description="Ativa ou desativa a tela cheia no YouTube",
        parameters=_no_params(),
        handler=lambda **_: youtube.control_video_playback("fullscreen"),
    )

    registry.register(
        name="youtube_skip_ad",
        description="Tenta pular o anúncio no YouTube",
        parameters=_no_params(),
        handler=lambda **_: youtube.attempt_skip_ad_selenium(),
    )

    registry.register(
        name="youtube_go_back",
        description="Volta para a página anterior no YouTube",
        parameters=_no_params(),
        handler=lambda **_: youtube.go_back_in_browser_history(),
    )


# ─────────────────────────────────────────────────────────────────────────────
# 4.4  WhatsAppService
# ─────────────────────────────────────────────────────────────────────────────

def register_whatsapp(registry: ToolRegistry, whatsapp):
    """Register WhatsAppService tools."""

    registry.register(
        name="send_whatsapp",
        description="Envia uma mensagem pelo WhatsApp para um contato",
        parameters=_schema(
            _param("contact", "string", "Nome do contato no WhatsApp"),
            _param("message", "string", "Conteúdo da mensagem a enviar"),
        ),
        handler=lambda contact, message: whatsapp.send_message(
            contact_name=contact, message=message
        ),
    )


# ─────────────────────────────────────────────────────────────────────────────
# 4.5  SystemService
# ─────────────────────────────────────────────────────────────────────────────

def register_system(registry: ToolRegistry, system):
    """Register SystemService tools."""

    registry.register(
        name="get_datetime",
        description="Retorna a data e hora atual do sistema",
        parameters=_no_params(),
        handler=lambda **_: system.get_current_datetime_string(),
    )

    registry.register(
        name="open_application",
        description=(
            "Abre um aplicativo instalado no computador. "
            "Use list_installed_apps primeiro se não tiver certeza do nome exato."
        ),
        parameters=_schema(
            _param("app_name", "string", "Nome do aplicativo a abrir"),
        ),
        handler=lambda app_name: system.open_application(app_name),
    )

    registry.register(
        name="list_installed_apps",
        description=(
            "Lista os aplicativos instalados no computador. "
            "Aceita um filtro opcional para restringir a busca (ex: 'adobe', 'game', 'browser')."
        ),
        parameters=_schema(
            _param("filter_query", "string", "Termo opcional para filtrar a lista (ex: 'game')", required=False),
        ),
        handler=lambda filter_query="": system.list_installed_apps(filter_query=filter_query),
    )

    registry.register(
        name="refresh_app_index",
        description=(
            "Atualiza a lista de aplicativos instalados escaneando o sistema novamente. "
            "Use quando o usuário instalar um novo programa e quiser abri-lo."
        ),
        parameters=_no_params(),
        handler=lambda **_: system.refresh_app_index(),
    )

    registry.register(
        name="search_web",
        description="Pesquisa um termo no Google via navegador padrão",
        parameters=_schema(
            _param("query", "string", "Termo a pesquisar na web"),
        ),
        handler=lambda query: system.search_web(query),
    )

    registry.register(
        name="set_system_volume",
        description="Ajusta o volume do sistema (0 a 100)",
        parameters=_schema(
            _param("level", "string", "Nível de volume, ex: '50', '75%'"),
        ),
        handler=lambda level: system.adjust_system_volume(volume_level_str=str(level)),
    )

    registry.register(
        name="start_timer",
        description="Inicia um timer/alarme em segundo plano",
        parameters=_schema(
            _param("duration", "string", "Duração do timer, ex: '5 minutos', '30 segundos'"),
        ),
        handler=lambda duration: system.start_timer(duration_str=duration),
    )


# ─────────────────────────────────────────────────────────────────────────────
# 4.6  AppInteractionService
# ─────────────────────────────────────────────────────────────────────────────

def register_app_interaction(registry: ToolRegistry, app_interaction):
    """Register AppInteractionService tools."""

    registry.register(
        name="list_running_apps",
        description=(
            "Lista as janelas/aplicativos abertos no momento no computador. "
            "Use para verificar se um app está rodando antes de interagir com ele."
        ),
        parameters=_no_params(),
        handler=lambda **_: app_interaction.list_running_apps(),
    )

    registry.register(
        name="focus_window",
        description="Traz a janela de um aplicativo aberto para frente (foco).",
        parameters=_schema(
            _param("app_name", "string", "Nome parcial do app ou título da janela (ex: 'Steam', 'Chrome')"),
        ),
        handler=lambda app_name: app_interaction.focus_window(app_name),
    )

    registry.register(
        name="vscode_open_folder",
        description=(
            "Abre uma pasta no VSCode. "
            "Pode reutilizar a janela atual ou abrir uma nova janela."
        ),
        parameters=_schema(
            _param("path", "string", "Caminho completo da pasta a abrir"),
            _param("new_window", "boolean", "Se true, abre em uma nova janela do VSCode", required=False),
        ),
        handler=lambda path, new_window=False: app_interaction.vscode_open_folder(
            path=path, new_window=bool(new_window)
        ),
    )

    registry.register(
        name="vscode_open_terminal",
        description=(
            "Abre uma pasta no VSCode e automaticamente abre o terminal integrado (Ctrl+`). "
            "Ideal para iniciar um projeto diretamente no terminal."
        ),
        parameters=_schema(
            _param("path", "string", "Caminho completo da pasta do projeto"),
        ),
        handler=lambda path: app_interaction.vscode_open_terminal(path=path),
    )

    registry.register(
        name="open_terminal_in_folder",
        description=(
            "Abre um terminal (Windows Terminal ou PowerShell) diretamente na pasta especificada. "
            "Use quando o usuário quiser um terminal avulso, não o terminal do VSCode."
        ),
        parameters=_schema(
            _param("path", "string", "Caminho completo da pasta onde abrir o terminal"),
        ),
        handler=lambda path: app_interaction.open_terminal_in_folder(path=path),
    )

    registry.register(
        name="find_and_open_project",
        description=(
            "USE ESTA FERRAMENTA quando o usuário pedir para abrir um projeto ou pasta no VSCode. "
            "Busca automaticamente a pasta nas pastas comuns do usuário "
            "(home, Documentos, Desktop, Downloads, Projects, repos, dev) pelo nome informado "
            "e abre no VSCode. "
            "Exemplos de quando usar: 'abre o projeto Marvin', 'abre meu portfólio no VSCode', "
            "'quero trabalhar no projeto landing-page'. "
            "NÃO use open_application nem vscode_open_folder para este caso."
        ),
        parameters=_schema(
            _param(
                "project_name",
                "string",
                (
                    "Nome (ou parte do nome) da pasta do projeto. "
                    "Se o usuário quiser abrir com terminal integrado, inclua 'com terminal' no valor, "
                    "ex: 'Marvin com terminal'."
                ),
            ),
        ),
        handler=lambda project_name: app_interaction.find_and_open_project(
            project_name=project_name
        ),
    )

    registry.register(
        name="steam_search_game",
        description=(
            "Abre o cliente Steam e mostra os resultados de busca para o jogo solicitado. "
            "Requer Steam instalado."
        ),
        parameters=_schema(
            _param("query", "string", "Nome do jogo a buscar na Steam"),
        ),
        handler=lambda query: app_interaction.steam_search_game(query=query),
    )

    registry.register(
        name="steam_find_game",
        description=(
            "Busca jogos na Steam Store pela API e retorna nome e App ID. "
            "Use para descobrir o App ID de um jogo antes de iniciá-lo com steam_launch_game."
        ),
        parameters=_schema(
            _param("query", "string", "Nome do jogo a buscar"),
        ),
        handler=lambda query: app_interaction.steam_find_game(query=query),
    )

    registry.register(
        name="steam_launch_game",
        description=(
            "Inicia um jogo da Steam pelo App ID. "
            "Use steam_find_game primeiro para descobrir o App ID a partir do nome do jogo."
        ),
        parameters=_schema(
            _param("app_id", "string", "App ID numérico do jogo na Steam (ex: '730' para CS2)"),
        ),
        handler=lambda app_id: app_interaction.steam_launch_game(app_id=str(app_id)),
    )


# ─────────────────────────────────────────────────────────────────────────────
# Convenience: registra tudo de uma vez
# ─────────────────────────────────────────────────────────────────────────────

# ─────────────────────────────────────────────────────────────────────────────
# 4.7  AppCapabilityService (profile-driven, dynamic)
# ─────────────────────────────────────────────────────────────────────────────

def register_app_capabilities(registry: ToolRegistry, capabilities):
    """
    Dynamically register all tools produced by AppCapabilityService.
    Each tool maps to one capability of one detected app.
    """
    # Meta-tool: list which apps have interaction support
    registry.register(
        name="list_supported_apps",
        description=(
            "Lista quais aplicativos instalados têm suporte de interação pelo Marvin "
            "e quais ações estão disponíveis para cada um."
        ),
        parameters=_no_params(),
        handler=lambda **_: capabilities.list_active_apps(),
    )

    registry.register(
        name="refresh_app_capabilities",
        description=(
            "Re-escaneia os aplicativos instalados e atualiza a lista de interações disponíveis. "
            "Use após instalar um novo programa."
        ),
        parameters=_no_params(),
        handler=lambda **_: capabilities.refresh(),
    )

    tools = capabilities.get_active_tools()
    for tool in tools:
        registry.register(
            name=tool["name"],
            description=tool["description"],
            parameters=tool["parameters"],
            handler=tool["handler"],
        )

    return len(tools)


def register_all(
    registry: ToolRegistry,
    spotify=None,
    youtube=None,
    whatsapp=None,
    system=None,
    app_interaction=None,
    app_capabilities=None,
) -> list[str]:
    """
    Register all available services. Skips services that are None.
    Returns list of registered tool names.
    """
    if spotify:
        try:
            register_spotify(registry, spotify)
            print("ServiceRegistrar: SpotifyService registrado (7 ferramentas).")
        except Exception as e:
            print(f"ServiceRegistrar: Falha ao registrar Spotify: {e}")

    if youtube:
        try:
            register_youtube(registry, youtube)
            print("ServiceRegistrar: YouTubeService registrado (6 ferramentas).")
        except Exception as e:
            print(f"ServiceRegistrar: Falha ao registrar YouTube: {e}")

    if whatsapp:
        try:
            register_whatsapp(registry, whatsapp)
            print("ServiceRegistrar: WhatsAppService registrado (1 ferramenta).")
        except Exception as e:
            print(f"ServiceRegistrar: Falha ao registrar WhatsApp: {e}")

    if system:
        try:
            register_system(registry, system)
            print("ServiceRegistrar: SystemService registrado (7 ferramentas).")
        except Exception as e:
            print(f"ServiceRegistrar: Falha ao registrar System: {e}")

    if app_interaction:
        try:
            register_app_interaction(registry, app_interaction)
            print("ServiceRegistrar: AppInteractionService registrado (7 ferramentas).")
        except Exception as e:
            print(f"ServiceRegistrar: Falha ao registrar AppInteraction: {e}")

    if app_capabilities:
        try:
            n = register_app_capabilities(registry, app_capabilities)
            print(f"ServiceRegistrar: AppCapabilityService registrado ({n} capabilities de apps detectados).")
        except Exception as e:
            print(f"ServiceRegistrar: Falha ao registrar AppCapabilities: {e}")

    return registry.list_names()
