# backend/app/ai/tool_registry.py
#
# ──────────────────────────────────────────────────────────────────────────────
# AUDITORIA DOS SERVIÇOS (Fase 4.1)
# ──────────────────────────────────────────────────────────────────────────────
# SpotifyService (spotipy)
#   play_music(track_name, device_id=None)           → dict {status, message}
#   pause_playback(device_id=None)                   → dict
#   resume_playback(device_id=None)                  → dict
#   next_track(device_id=None)                       → dict
#   previous_track(device_id=None)                   → dict
#   list_user_playlists()                            → list[dict]
#   play_playlist(playlist_identifier, mode, ...)    → dict
#   list_available_devices()                         → list[dict]
#   NOTE: sem get_current_track nem set_volume — wrappers em service_registrar.py
#
# YouTubeService (selenium)
#   search_youtube(query)                            → dict
#   click_video_by_position(position)                → dict
#   control_video_playback(action)                   → dict
#     actions: 'toggle_pause_play' | 'fullscreen' | 'exit_fullscreen' | 'maximize_window'
#   attempt_skip_ad_selenium()                       → dict
#   go_back_in_browser_history()                     → dict
#
# WhatsAppService (pyautogui + webbrowser)
#   send_message(contact_name, message)              → dict
#
# SystemService
#   get_current_datetime_string()                    → dict {status, message, time, date}
#   open_application(app_name)                       → dict
#   open_calculator()                                → dict
#   search_web(query)                                → dict
#   start_timer(duration_str)                        → dict   e.g. "5 minutos"
#   adjust_system_volume(volume_level_str)           → dict   e.g. "50" ou "75%"
# ──────────────────────────────────────────────────────────────────────────────

import json
from typing import Any, Callable


class ToolRegistry:
    """
    Registry of callable tools exposed to the LLM as function-calling definitions.

    Each tool entry:
        name        – unique identifier (snake_case)
        description – what the LLM reads to decide when to call the tool
        parameters  – JSON-Schema object describing the arguments
        handler     – Python callable that executes the action
    """

    def __init__(self):
        self._tools: dict[str, dict] = {}

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def register(
        self,
        name: str,
        description: str,
        parameters: dict,
        handler: Callable,
    ):
        """Register a new tool. Overwrites if name already exists."""
        self._tools[name] = {
            "name": name,
            "description": description,
            "parameters": parameters,
            "handler": handler,
        }

    # ------------------------------------------------------------------
    # LLM-facing schema
    # ------------------------------------------------------------------

    def get_tools_schema(self) -> list[dict]:
        """
        Returns the list of tool definitions in OpenAI/Groq function-calling format.
        """
        return [
            {
                "type": "function",
                "function": {
                    "name": t["name"],
                    "description": t["description"],
                    "parameters": t["parameters"],
                },
            }
            for t in self._tools.values()
        ]

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------

    def execute(self, name: str, arguments: str | dict) -> str:
        """
        Execute a registered tool by name.

        Args:
            name:      Tool name as returned by the LLM.
            arguments: JSON string or dict of arguments from the LLM.

        Returns:
            String result to feed back to the LLM as a tool message.
        """
        if name not in self._tools:
            return f"Erro: ferramenta '{name}' não encontrada no registro."

        if isinstance(arguments, str):
            try:
                parsed = json.loads(arguments)
                # Groq sends null for no-param tools; treat as empty dict
                kwargs = parsed if isinstance(parsed, dict) else {}
            except json.JSONDecodeError as e:
                return f"Erro ao decodificar argumentos para '{name}': {e}"
        elif arguments is None:
            kwargs = {}
        else:
            kwargs = arguments

        try:
            result = self._tools[name]["handler"](**kwargs)
            # Services return dicts with a "message" key; flatten to string.
            if isinstance(result, dict):
                return result.get("message", str(result))
            return str(result)
        except Exception as e:
            return f"Erro ao executar '{name}': {e}"

    def has_tool(self, name: str) -> bool:
        return name in self._tools

    def list_names(self) -> list[str]:
        return list(self._tools.keys())
