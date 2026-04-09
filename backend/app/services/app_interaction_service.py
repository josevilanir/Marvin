# backend/app/services/app_interaction_service.py
"""
AppInteractionService — interacts with RUNNING applications on Windows.

Capabilities:
  - List open windows / running apps
  - Focus any window by app name
  - VSCode: open folder, open in new window, open with integrated terminal
  - Steam: search game in client, find game IDs via Store API, launch game by ID
"""
import os
import subprocess
import shutil
import time
import ctypes
import difflib
from ctypes import wintypes
from pathlib import Path

import psutil
import requests

# Directories to search for projects, in priority order.
# %USERPROFILE% resolves to C:\Users\<username>
_PROJECT_SEARCH_ROOTS = [
    os.path.expandvars(r"%USERPROFILE%"),
    os.path.expandvars(r"%USERPROFILE%\Projects"),
    os.path.expandvars(r"%USERPROFILE%\project"),
    os.path.expandvars(r"%USERPROFILE%\repos"),
    os.path.expandvars(r"%USERPROFILE%\dev"),
    os.path.expandvars(r"%USERPROFILE%\Documents"),
    os.path.expandvars(r"%USERPROFILE%\Desktop"),
    os.path.expandvars(r"%USERPROFILE%\Downloads"),
]

# Folders inside %USERPROFILE% that are never a project themselves
_SKIP_NAMES = {
    "appdata", ".vscode", ".ssh", ".git", "desktop", "downloads",
    "documents", "pictures", "videos", "music", "3d objects",
    "contacts", "favorites", "links", "saved games", "searches",
    "onedrive", "projects", "project", "repos", "dev", "node_modules",
    "site-packages", "__pycache__",
}


# ─── Win32 window helpers (ctypes only, no pywin32 dep) ──────────────────────

def _enum_windows() -> list[tuple[int, str]]:
    """Return list of (hwnd, title) for all visible, titled windows."""
    results = []

    def _callback(hwnd, _):
        if ctypes.windll.user32.IsWindowVisible(hwnd):
            length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
            if length > 0:
                buf = ctypes.create_unicode_buffer(length + 1)
                ctypes.windll.user32.GetWindowTextW(hwnd, buf, length + 1)
                results.append((hwnd, buf.value))
        return True

    WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    ctypes.windll.user32.EnumWindows(WNDENUMPROC(_callback), 0)
    return results


def _bring_window_to_front(hwnd: int):
    SW_RESTORE = 9
    ctypes.windll.user32.ShowWindow(hwnd, SW_RESTORE)
    ctypes.windll.user32.SetForegroundWindow(hwnd)


# ─────────────────────────────────────────────────────────────────────────────

class AppInteractionService:
    """
    Provides tools for interacting with applications that are currently
    running or can be launched on Windows.
    """

    # ── General window management ─────────────────────────────────────────

    def list_running_apps(self) -> dict:
        """
        Returns a deduplicated list of visible window titles (= open apps).
        """
        windows = _enum_windows()
        titles = sorted({title for _, title in windows if title.strip()})
        if not titles:
            return {"status": "info", "message": "Nenhuma janela aberta encontrada."}
        display = titles[:25]
        extra = f" (+{len(titles) - 25} outros)" if len(titles) > 25 else ""
        return {
            "status": "success",
            "message": f"Janelas abertas ({len(titles)}{extra}): " + " | ".join(display),
            "windows": titles,
        }

    def focus_window(self, app_name: str) -> dict:
        """
        Brings the first window whose title contains `app_name` to the foreground.
        """
        query = app_name.lower()
        windows = _enum_windows()
        matches = [(hwnd, title) for hwnd, title in windows if query in title.lower()]

        if not matches:
            return {
                "status": "error",
                "message": f"Nenhuma janela aberta com o nome '{app_name}' foi encontrada.",
            }

        hwnd, title = matches[0]
        try:
            _bring_window_to_front(hwnd)
            return {"status": "success", "message": f"Janela '{title}' trazida para frente."}
        except Exception as e:
            return {"status": "error", "message": f"Erro ao focar janela '{title}': {e}"}

    # ── VSCode ────────────────────────────────────────────────────────────

    def _vscode_cmd(self) -> str | None:
        """Returns the path to the VSCode CLI, or None if not found."""
        return shutil.which("code") or shutil.which("code.cmd")

    def vscode_open_folder(self, path: str, new_window: bool = False) -> dict:
        """
        Opens a folder in VSCode.
        `new_window=True` forces a new VSCode window instead of reusing the current one.
        """
        code = self._vscode_cmd()
        if not code:
            return {
                "status": "error",
                "message": (
                    "VSCode CLI ('code') não encontrado. "
                    "Certifique-se de que o VSCode está instalado e o comando 'code' está no PATH."
                ),
            }

        path = os.path.expandvars(os.path.expanduser(path))
        if not os.path.exists(path):
            return {"status": "error", "message": f"Caminho não encontrado: '{path}'"}

        flag = "--new-window" if new_window else "--reuse-window"
        try:
            subprocess.Popen([code, flag, path])
            action = "nova janela do " if new_window else ""
            return {
                "status": "success",
                "message": f"Abrindo '{path}' em {action}VSCode.",
            }
        except Exception as e:
            return {"status": "error", "message": f"Erro ao abrir VSCode: {e}"}

    def vscode_open_terminal(self, path: str) -> dict:
        """
        Opens a folder in VSCode and then opens the integrated terminal (Ctrl+`).
        Requires VSCode to be installed with the 'code' CLI in PATH.
        """
        result = self.vscode_open_folder(path, new_window=False)
        if result["status"] != "success":
            return result

        try:
            import pyautogui
            time.sleep(2.5)  # wait for VSCode to load and take focus

            # Focus VSCode window
            focus = self.focus_window("Visual Studio Code")
            if focus["status"] != "success":
                # VSCode might show project name in title — try generic
                self.focus_window("Code")
            time.sleep(0.4)

            pyautogui.hotkey("ctrl", "`")
            return {
                "status": "success",
                "message": f"Pasta '{path}' aberta no VSCode com terminal integrado.",
            }
        except Exception as e:
            print(f"AppInteraction: erro ao abrir terminal no VSCode: {e}")
            return {
                "status": "partial",
                "message": (
                    f"Pasta '{path}' aberta no VSCode. "
                    "Para abrir o terminal integrado, pressione Ctrl+` (backtick)."
                ),
            }

    # ── Project finder ────────────────────────────────────────────────────

    def find_and_open_project(self, project_name: str) -> dict:
        """
        Searches common directories for a folder matching `project_name` and
        opens it in VSCode.

        Search roots (in order): user home, Projects, repos, dev, Documents,
        Desktop, Downloads.  Immediate subdirectories are fuzzy-matched against
        the requested name using difflib.  A score ≥ 0.7 is opened
        automatically; 0.4–0.7 prompts the user with the top candidates.
        """
        if not project_name.strip():
            return {"status": "error", "message": "Nenhum nome de projeto fornecido."}

        # Detect "com terminal" intent embedded in the name string
        _terminal_markers = ("com terminal", "with terminal", "abre terminal", "open terminal")
        open_terminal = any(m in project_name.lower() for m in _terminal_markers)
        for m in _terminal_markers:
            project_name = project_name.lower().replace(m, "").strip(" ,")

        query = project_name.strip().lower()
        candidates: list[tuple[float, str]] = []  # (score, path)
        print(f"ProjectFinder: buscando '{query}'...")

        seen_paths: set[str] = set()

        for root in _PROJECT_SEARCH_ROOTS:
            if not os.path.isdir(root):
                continue
            try:
                entries = os.scandir(root)
            except PermissionError:
                continue

            for entry in entries:
                if not entry.is_dir(follow_symlinks=False):
                    continue
                norm_name = entry.name.lower()
                if norm_name in _SKIP_NAMES:
                    continue
                abs_path = str(Path(entry.path).resolve())
                if abs_path in seen_paths:
                    continue
                seen_paths.add(abs_path)

                # Score: exact match → 1.0, otherwise sequence ratio
                if norm_name == query:
                    score = 1.0
                else:
                    score = difflib.SequenceMatcher(None, query, norm_name).ratio()
                    # Boost if query is a substring of the folder name
                    if query in norm_name:
                        score = max(score, 0.75)

                if score >= 0.35:
                    candidates.append((score, abs_path))

        if not candidates:
            return {
                "status": "error",
                "message": (
                    f"Nenhuma pasta chamada '{project_name}' encontrada nas pastas de projetos. "
                    "Verifique o nome ou informe o caminho completo."
                ),
            }

        # Sort by score descending
        candidates.sort(key=lambda x: x[0], reverse=True)
        best_score, best_path = candidates[0]

        print(f"ProjectFinder: top candidatos:")
        for sc, p in candidates[:5]:
            print(f"  score={sc:.2f}  {p}")

        # High confidence — open directly
        if best_score >= 0.7:
            action_fn = self.vscode_open_terminal if open_terminal else self.vscode_open_folder
            result = action_fn(best_path)
            result["message"] = f"Projeto encontrado em '{best_path}'. " + result.get("message", "")
            return result

        # Medium confidence — show top options
        top = candidates[:4]
        names = [os.path.basename(p) for _, p in top]
        return {
            "status": "ambiguous",
            "message": (
                f"Encontrei várias pastas parecidas com '{project_name}': "
                + ", ".join(f"'{n}'" for n in names)
                + ". Qual delas você quer abrir no VSCode?"
            ),
            "candidates": [p for _, p in top],
        }

    # ── Open terminal in folder (standalone) ─────────────────────────────

    def open_terminal_in_folder(self, path: str) -> dict:
        """
        Opens a terminal window (Windows Terminal, then PowerShell as fallback)
        with the working directory set to `path`.
        """
        path = os.path.expandvars(os.path.expanduser(path))
        if not os.path.exists(path):
            return {"status": "error", "message": f"Caminho não encontrado: '{path}'"}

        # Try Windows Terminal first, then PowerShell, then cmd
        for cmd, args in [
            ("wt.exe", ["wt.exe", "--startingDirectory", path]),
            ("powershell.exe", ["powershell.exe", "-NoExit", "-Command", f'Set-Location "{path}"']),
            ("cmd.exe", ["cmd.exe", "/k", f'cd /d "{path}"']),
        ]:
            if shutil.which(cmd):
                try:
                    subprocess.Popen(args)
                    return {
                        "status": "success",
                        "message": f"Terminal aberto em '{path}'.",
                    }
                except Exception as e:
                    print(f"AppInteraction: falha com {cmd}: {e}")
                    continue

        return {"status": "error", "message": "Nenhum terminal disponível (wt, powershell, cmd)."}

    # ── Steam ─────────────────────────────────────────────────────────────

    def steam_search_game(self, query: str) -> dict:
        """
        Opens the Steam client and navigates to the search results for `query`.
        Steam must be installed on the system.
        """
        if not query.strip():
            return {"status": "error", "message": "Nenhum termo de busca fornecido."}
        try:
            uri = f"steam://search/{query}"
            os.startfile(uri)
            return {
                "status": "success",
                "message": f"Abrindo busca no Steam por '{query}'.",
            }
        except Exception as e:
            return {"status": "error", "message": f"Erro ao abrir Steam: {e}"}

    def steam_find_game(self, query: str) -> dict:
        """
        Searches the Steam Store API for games matching `query`.
        Returns a list of games with their names and App IDs (useful for steam_launch_game).
        No API key required.
        """
        if not query.strip():
            return {"status": "error", "message": "Nenhum termo de busca fornecido."}
        try:
            resp = requests.get(
                "https://store.steampowered.com/api/storesearch/",
                params={"term": query, "l": "portuguese", "cc": "BR"},
                timeout=6,
            )
            resp.raise_for_status()
            data = resp.json()
            items = data.get("items", [])[:6]
            if not items:
                return {"status": "info", "message": f"Nenhum jogo encontrado para '{query}' na Steam."}

            games = [{"name": g["name"], "app_id": g["id"]} for g in items]
            summary = ", ".join(f"{g['name']} (ID: {g['app_id']})" for g in games)
            return {
                "status": "success",
                "message": f"Jogos encontrados na Steam: {summary}",
                "games": games,
            }
        except requests.RequestException as e:
            return {"status": "error", "message": f"Erro ao consultar a Steam Store: {e}"}

    def steam_launch_game(self, app_id: str) -> dict:
        """
        Launches a Steam game directly by its App ID.
        Use `steam_find_game` first to discover the App ID from a game name.
        """
        if not str(app_id).strip().isdigit():
            return {"status": "error", "message": f"App ID inválido: '{app_id}'. Deve ser um número."}
        try:
            uri = f"steam://run/{app_id}"
            os.startfile(uri)
            return {
                "status": "success",
                "message": f"Iniciando jogo Steam (App ID: {app_id}) via Steam client.",
            }
        except Exception as e:
            return {"status": "error", "message": f"Erro ao iniciar jogo na Steam: {e}"}
