# backend/app/services/app_discovery.py
"""
Discovers installed applications on Windows by scanning:
  - Registry App Paths  (direct exe-name → full path mapping)
  - Registry Uninstall  (HKLM + HKCU, 32 and 64-bit)
  - Start Menu shortcuts (.lnk files, recursive)
  - Desktop shortcuts   (.lnk files)

Results are cached in data/app_index.json and rebuilt after 24h or on demand.
"""
import os
import json
import time
import difflib
from pathlib import Path

try:
    import winreg
    _WINREG = True
except ImportError:
    _WINREG = False

# data/app_index.json sits at Marvin/data/ — 3 levels up from this file
_DATA_DIR = Path(__file__).resolve().parents[3] / "data"
_CACHE_FILE = _DATA_DIR / "app_index.json"
_CACHE_MAX_AGE = 24 * 3600  # seconds

# Words that indicate helper/updater executables to skip
_SKIP_WORDS = ("uninstall", "update", "crash", "helper", "setup", "installer", "repair")


class AppDiscovery:
    """
    Builds and queries a dynamic index of installed applications.
    Thread-safe for reads. Writes happen at startup or on explicit refresh().
    """

    def __init__(self):
        self._index: list[dict] = []
        self._load_or_build()

    # ─────────────────────────────────────────────────────────────────────────
    # Public API
    # ─────────────────────────────────────────────────────────────────────────

    def search(self, query: str, top_n: int = 5) -> list[dict]:
        """
        Fuzzy-search the index for apps matching `query`.
        Returns up to `top_n` deduplicated results sorted by score (highest first).
        Each item: {display_name, exe_path, source, score}
        """
        if not self._index:
            return []

        q = _normalize(query)
        scored = []
        for entry in self._index:
            s = _score(q, entry)
            if s > 0.3:
                scored.append({**entry, "score": round(s, 3)})

        scored.sort(key=lambda x: x["score"], reverse=True)

        # Deduplicate by normalized display_name — keep highest-scored entry
        seen: set[str] = set()
        unique = []
        for item in scored:
            key = _normalize(item["display_name"])
            if key not in seen:
                seen.add(key)
                unique.append(item)

        return unique[:top_n]

    def list_all(self, filter_query: str = "") -> list[dict]:
        """Return all indexed apps, optionally filtered by a case-insensitive substring."""
        if not filter_query:
            return list(self._index)
        q = filter_query.lower()
        return [e for e in self._index if q in e["display_name"].lower()]

    def refresh(self) -> int:
        """Force a full rescan. Returns the number of apps indexed."""
        self._index = _build_index()
        _save_cache(self._index)
        return len(self._index)

    def count(self) -> int:
        return len(self._index)

    # ─────────────────────────────────────────────────────────────────────────
    # Internal
    # ─────────────────────────────────────────────────────────────────────────

    def _load_or_build(self):
        cached = _load_cache()
        if cached is not None:
            self._index = cached
            print(f"AppDiscovery: carregados {len(cached)} apps do cache.")
        else:
            self._index = _build_index()
            _save_cache(self._index)


# ─────────────────────────────────────────────────────────────────────────────
# Cache helpers
# ─────────────────────────────────────────────────────────────────────────────

def _load_cache() -> list[dict] | None:
    if not _CACHE_FILE.exists():
        return None
    if time.time() - _CACHE_FILE.stat().st_mtime > _CACHE_MAX_AGE:
        return None
    try:
        with open(_CACHE_FILE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def _save_cache(index: list[dict]):
    try:
        _DATA_DIR.mkdir(parents=True, exist_ok=True)
        with open(_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(index, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"AppDiscovery: falha ao salvar cache: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# Index builder
# ─────────────────────────────────────────────────────────────────────────────

def _build_index() -> list[dict]:
    print("AppDiscovery: escaneando aplicativos instalados...")
    entries: dict[str, dict] = {}  # keyed by exe_path.lower() to deduplicate

    if _WINREG:
        _scan_app_paths(entries)
        _scan_uninstall(entries, winreg.HKEY_LOCAL_MACHINE)
        _scan_uninstall(entries, winreg.HKEY_CURRENT_USER)

    _scan_windows_store_apps(entries)
    _scan_shortcuts(entries, _start_menu_dirs())
    _scan_shortcuts(entries, [_desktop_dir()])

    result = list(entries.values())
    print(f"AppDiscovery: {len(result)} apps indexados.")
    return result


def _add(entries: dict, display_name: str, exe_path: str, source: str):
    if not display_name or not exe_path:
        return
    key = exe_path.lower()
    if key not in entries:
        entries[key] = {
            "display_name": display_name.strip(),
            "exe_path": exe_path,
            "source": source,
            "keywords": _extract_keywords(display_name),
        }


# ── Registry: App Paths ──────────────────────────────────────────────────────

def _scan_app_paths(entries: dict):
    """HKLM\\...\\App Paths\\*.exe  →  direct name-to-path mapping."""
    reg_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths"
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path) as base:
            i = 0
            while True:
                try:
                    sub_name = winreg.EnumKey(base, i)
                    i += 1
                    with winreg.OpenKey(base, sub_name) as sub:
                        try:
                            exe_path, _ = winreg.QueryValueEx(sub, "")
                            exe_path = exe_path.strip().strip('"')
                            display_name = sub_name
                            for ext in (".exe", ".EXE"):
                                display_name = display_name.replace(ext, "")
                            if exe_path and os.path.isfile(exe_path):
                                _add(entries, display_name, exe_path, "app_paths")
                        except FileNotFoundError:
                            pass
                except OSError:
                    break
    except Exception as e:
        print(f"AppDiscovery: erro ao ler App Paths: {e}")


# ── Registry: Uninstall ──────────────────────────────────────────────────────

def _scan_uninstall(entries: dict, hive):
    hive_name = "hklm" if hive == winreg.HKEY_LOCAL_MACHINE else "hkcu"
    reg_paths = [
        r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
        r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall",
    ]
    for reg_path in reg_paths:
        try:
            with winreg.OpenKey(hive, reg_path) as base:
                i = 0
                while True:
                    try:
                        sub_name = winreg.EnumKey(base, i)
                        i += 1
                        with winreg.OpenKey(base, sub_name) as sub:
                            try:
                                display_name, _ = winreg.QueryValueEx(sub, "DisplayName")
                            except FileNotFoundError:
                                continue

                            exe_path = _exe_from_uninstall_key(sub, display_name)
                            if exe_path:
                                _add(entries, display_name, exe_path, f"uninstall_{hive_name}")
                    except OSError:
                        break
        except Exception:
            pass


def _exe_from_uninstall_key(sub_key, display_name: str) -> str | None:
    # Method 1: InstallLocation directory → find main exe
    try:
        loc, _ = winreg.QueryValueEx(sub_key, "InstallLocation")
        if loc and os.path.isdir(loc):
            exe = _find_main_exe(loc, display_name)
            if exe:
                return exe
    except FileNotFoundError:
        pass

    # Method 2: DisplayIcon often is "C:\path\app.exe,0"
    try:
        icon, _ = winreg.QueryValueEx(sub_key, "DisplayIcon")
        icon_path = icon.split(",")[0].strip().strip('"')
        if icon_path.lower().endswith(".exe") and os.path.isfile(icon_path):
            # Skip if it looks like an uninstaller
            if not any(w in icon_path.lower() for w in _SKIP_WORDS):
                return icon_path
    except FileNotFoundError:
        pass

    return None


def _find_main_exe(install_dir: str, app_name: str) -> str | None:
    """Find the most plausible main exe inside install_dir (one level deep)."""
    app_norm = _normalize(app_name)
    candidates = []
    try:
        for entry in os.scandir(install_dir):
            if entry.is_file() and entry.name.lower().endswith(".exe"):
                if any(w in entry.name.lower() for w in _SKIP_WORDS):
                    continue
                score = difflib.SequenceMatcher(
                    None, app_norm, _normalize(entry.name)
                ).ratio()
                candidates.append((score, entry.path))
    except (PermissionError, OSError):
        return None

    if not candidates:
        return None
    candidates.sort(reverse=True)
    return candidates[0][1]


# ── Shortcuts ────────────────────────────────────────────────────────────────

def _scan_windows_store_apps(entries: dict):
    """Scan %LOCALAPPDATA%\\Microsoft\\WindowsApps for Store/UWP app stubs."""
    wa_dir = os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WindowsApps")
    if not os.path.isdir(wa_dir):
        return
    try:
        for entry in os.scandir(wa_dir):
            if entry.is_file() and entry.name.lower().endswith(".exe"):
                if any(w in entry.name.lower() for w in _SKIP_WORDS):
                    continue
                display_name = entry.name[:-4]  # strip .exe
                _add(entries, display_name, entry.path, "windows_store")
    except (PermissionError, OSError) as e:
        print(f"AppDiscovery: erro ao ler WindowsApps: {e}")


def _scan_shortcuts(entries: dict, dirs: list[str]):
    """Collect .lnk files — os.startfile() can launch them directly."""
    for base_dir in dirs:
        if not base_dir or not os.path.isdir(base_dir):
            continue
        for root, _, files in os.walk(base_dir):
            for fname in files:
                if fname.lower().endswith(".lnk"):
                    display_name = fname[:-4]
                    lnk_path = os.path.join(root, fname)
                    _add(entries, display_name, lnk_path, "shortcut")


def _start_menu_dirs() -> list[str]:
    return [
        os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Start Menu\Programs"),
        os.path.expandvars(r"%ProgramData%\Microsoft\Windows\Start Menu\Programs"),
    ]


def _desktop_dir() -> str:
    return os.path.expandvars(r"%USERPROFILE%\Desktop")


# ─────────────────────────────────────────────────────────────────────────────
# Text helpers
# ─────────────────────────────────────────────────────────────────────────────

def _normalize(text: str) -> str:
    text = text.lower()
    for ch in (".", "-", "_", "(", ")", "[", "]", ",", "!", "®", "™", "©"):
        text = text.replace(ch, " ")
    return " ".join(text.split())


_STOP_WORDS = {
    "o", "a", "os", "as", "de", "do", "da", "dos", "das",
    "em", "no", "na", "nos", "nas", "que", "e", "ou", "para",
    "por", "com", "um", "uma", "the", "and", "or", "for", "of",
    "in", "on", "at", "to", "is", "it",
}


def _extract_keywords(display_name: str) -> list[str]:
    words = _normalize(display_name).split()
    # Keep only meaningful words (length >= 3 and not stop words)
    return list(set(w for w in words if len(w) >= 3 and w not in _STOP_WORDS))


def _score(query: str, entry: dict) -> float:
    """
    Relevance score between 0 and 1.
    Priority: exact substring > all words match > any word match > fuzzy ratio.
    """
    name_norm = _normalize(entry["display_name"])
    keywords: list[str] = entry.get("keywords", [])
    q_words = query.split()

    if query == name_norm:
        return 1.0

    if query in name_norm:
        return 0.95

    # Every query word appears somewhere in the name/keywords
    if q_words and all(
        any(qw in kw for kw in [name_norm] + keywords) for qw in q_words
    ):
        return 0.85

    # At least one query word is an exact keyword
    if any(qw in keywords for qw in q_words):
        return 0.70

    # Partial word overlap
    kw_set = set(keywords)
    overlap = sum(1 for qw in q_words if qw in kw_set)
    if overlap:
        return 0.5 + 0.1 * (overlap / max(len(q_words), 1))

    # Fuzzy fallback
    return difflib.SequenceMatcher(None, query, name_norm).ratio()
