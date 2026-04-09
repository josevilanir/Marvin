# backend/app/services/app_capability_service.py
"""
AppCapabilityService — profile-driven app interaction engine.

Reads data/app_profiles.json, detects which apps are installed,
and exposes a dynamic list of LLM tool definitions — one per capability.

Adding a new app requires only editing app_profiles.json, no Python changes.

Capability types supported:
  cli  — runs subprocess.Popen([command, *interpolated_args], cwd=...)
  uri  — calls os.startfile(interpolated_uri)
"""
import json
import os
import re
import shutil
import subprocess
from pathlib import Path

from app.services.app_discovery import AppDiscovery

_PROFILES_PATH = Path(__file__).resolve().parents[3] / "data" / "app_profiles.json"


def _load_profiles() -> dict:
    try:
        with open(_PROFILES_PATH, encoding="utf-8") as f:
            raw = json.load(f)
        # Strip meta keys (start with "_")
        return {k: v for k, v in raw.items() if not k.startswith("_")}
    except Exception as e:
        print(f"AppCapabilityService: erro ao carregar perfis: {e}")
        return {}


def _interpolate(template: str, params: dict) -> str:
    """Replace {param} placeholders in a string with actual values."""
    for key, value in params.items():
        template = template.replace(f"{{{key}}}", str(value))
    return template


class AppCapabilityService:
    """
    Detects which apps from the profile catalog are installed and provides
    callable handlers for their capabilities.

    Usage:
        service = AppCapabilityService()
        for tool in service.get_active_tools():
            registry.register(tool["name"], tool["description"],
                               tool["parameters"], tool["handler"])
    """

    def __init__(self, app_discovery: AppDiscovery | None = None):
        self._profiles = _load_profiles()
        self._discovery = app_discovery or AppDiscovery()
        self._active: dict[str, dict] = {}  # app_id → profile
        self._detect_installed()

    # ── Detection ─────────────────────────────────────────────────────────

    def _detect_installed(self):
        detected = []
        for app_id, profile in self._profiles.items():
            detect = profile.get("detect", {})
            installed = False

            # Method 1: CLI in PATH
            if cli := detect.get("cli"):
                if shutil.which(cli):
                    installed = True

            # Method 2: App name in AppDiscovery index (registry/shortcuts)
            if not installed and (app_name := detect.get("app_name")):
                results = self._discovery.search(app_name, top_n=1)
                if results and results[0]["score"] >= 0.65:
                    installed = True

            if installed:
                self._active[app_id] = profile
                detected.append(profile.get("display_name", app_id))

        if detected:
            print(f"AppCapabilityService: {len(detected)} apps detectados: {', '.join(detected)}")
        else:
            print("AppCapabilityService: nenhum app do catálogo detectado.")

    # ── Tool generation ───────────────────────────────────────────────────

    def get_active_tools(self) -> list[dict]:
        """
        Returns a list of tool definitions for all detected apps.
        Each entry: {name, description, parameters (JSON Schema), handler}
        """
        tools = []
        for app_id, profile in self._active.items():
            for cap in profile.get("capabilities", []):
                tools.append({
                    "name": f"{app_id}_{cap['id']}",
                    "description": cap["description"],
                    "parameters": _build_schema(cap.get("params", [])),
                    "handler": self._make_handler(app_id, cap),
                })
        return tools

    def get_active_profiles(self) -> list[dict]:
        """
        Returns structured data for GUI visualization.
        Each entry: {app_id, display_name, detected_by, capabilities[{tool_name, id, description, type, params}]}
        """
        result = []
        for app_id, profile in self._active.items():
            detect = profile.get("detect", {})
            detected_by = "cli" if detect.get("cli") and shutil.which(detect["cli"]) else "sistema"
            caps = []
            for cap in profile.get("capabilities", []):
                caps.append({
                    "id": cap["id"],
                    "tool_name": f"{app_id}_{cap['id']}",
                    "description": cap.get("description", ""),
                    "type": cap.get("type", "cli"),
                    "params": cap.get("params", []),
                    "template": cap.get("uri") or " ".join([cap.get("command", "")] + cap.get("args", [])),
                })
            result.append({
                "app_id": app_id,
                "display_name": profile.get("display_name", app_id),
                "detected_by": detected_by,
                "capabilities": caps,
            })
        return result

    def list_active_apps(self) -> dict:
        """Returns a summary of detected apps and their available capabilities."""
        if not self._active:
            return {
                "status": "info",
                "message": "Nenhum app do catálogo foi detectado como instalado.",
            }
        lines = []
        for app_id, profile in self._active.items():
            caps = [c["id"] for c in profile.get("capabilities", [])]
            lines.append(f"{profile.get('display_name', app_id)}: {', '.join(caps)}")
        return {
            "status": "success",
            "message": "Apps com suporte de interação instalados:\n" + "\n".join(lines),
            "apps": list(self._active.keys()),
        }

    def refresh(self) -> dict:
        """Re-scan which apps are installed and rebuild the active list."""
        self._active.clear()
        self._detect_installed()
        return self.list_active_apps()

    # ── Execution ─────────────────────────────────────────────────────────

    def _make_handler(self, app_id: str, cap: dict):
        """Closure that captures app_id and cap for deferred execution."""
        def handler(**kwargs):
            return self._execute(app_id, cap, **kwargs)
        return handler

    def _execute(self, app_id: str, cap: dict, **kwargs) -> dict:
        cap_type = cap.get("type")
        display = self._active[app_id].get("display_name", app_id)

        try:
            if cap_type == "cli":
                return self._execute_cli(cap, display, kwargs)
            elif cap_type == "uri":
                return self._execute_uri(cap, display, kwargs)
            else:
                return {"status": "error", "message": f"Tipo de capability desconhecido: '{cap_type}'"}
        except Exception as e:
            return {
                "status": "error",
                "message": f"Erro ao executar '{cap['id']}' em {display}: {e}",
            }

    def _execute_cli(self, cap: dict, display: str, kwargs: dict) -> dict:
        command = cap["command"]
        resolved_cmd = shutil.which(command)
        if not resolved_cmd:
            # Try AppDiscovery as fallback for GUI apps
            results = self._discovery.search(display, top_n=1)
            if results and results[0]["score"] >= 0.65:
                resolved_cmd = results[0]["exe_path"]
            else:
                return {
                    "status": "error",
                    "message": (
                        f"Comando '{command}' não encontrado no PATH. "
                        f"Verifique se o {display} está instalado corretamente."
                    ),
                }

        args = [_interpolate(arg, kwargs) for arg in cap.get("args", [])]
        cwd = _interpolate(cap["cwd"], kwargs) if "cwd" in cap else None

        if cwd and not os.path.exists(cwd):
            return {"status": "error", "message": f"Diretório não encontrado: '{cwd}'"}

        subprocess.Popen([resolved_cmd] + args, cwd=cwd or None)
        response = _interpolate(cap.get("response", f"{display}: OK."), kwargs)
        return {"status": "success", "message": response}

    def _execute_uri(self, cap: dict, display: str, kwargs: dict) -> dict:
        uri = _interpolate(cap["uri"], kwargs)
        os.startfile(uri)
        response = _interpolate(cap.get("response", f"{display}: OK."), kwargs)
        return {"status": "success", "message": response}


# ── Schema builder ────────────────────────────────────────────────────────────

def _build_schema(params: list[dict]) -> dict:
    """Convert profile param definitions to JSON Schema for the LLM."""
    properties = {}
    required = []
    for p in params:
        properties[p["name"]] = {
            "type": p.get("type", "string"),
            "description": p.get("description", ""),
        }
        if p.get("required", True):
            required.append(p["name"])
    return {"type": "object", "properties": properties, "required": required}
