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
        description="Abre um aplicativo no computador (ex: calculadora, bloco de notas, spotify)",
        parameters=_schema(
            _param("app_name", "string", "Nome do aplicativo a abrir"),
        ),
        handler=lambda app_name: system.open_application(app_name),
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
# Convenience: registra tudo de uma vez
# ─────────────────────────────────────────────────────────────────────────────

def register_all(
    registry: ToolRegistry,
    spotify=None,
    youtube=None,
    whatsapp=None,
    system=None,
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
            print("ServiceRegistrar: SystemService registrado (5 ferramentas).")
        except Exception as e:
            print(f"ServiceRegistrar: Falha ao registrar System: {e}")

    return registry.list_names()
