# backend/app/ai/system_observer.py
import ctypes
import ctypes.wintypes
import threading
import time
import psutil


def _get_active_window_info() -> tuple[str, str]:
    """Return (process_name, window_title) of the foreground window (Windows only)."""
    try:
        hwnd = ctypes.windll.user32.GetForegroundWindow()

        # Window title
        length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
        buf = ctypes.create_unicode_buffer(length + 1)
        ctypes.windll.user32.GetWindowTextW(hwnd, buf, length + 1)
        title = buf.value

        # Process name
        pid = ctypes.wintypes.DWORD()
        ctypes.windll.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        proc = psutil.Process(pid.value)
        return proc.name(), title
    except Exception:
        return "unknown", ""


class SystemObserver:
    """
    Collects system metrics in a background daemon thread.
    Thread-safe: all state access protected by _lock.
    """

    def __init__(self, interval_seconds: int = 5):
        self._interval = interval_seconds
        self._lock = threading.Lock()
        self._running = False
        self._thread: threading.Thread | None = None

        # Warm up cpu_percent (first call always returns 0.0)
        psutil.cpu_percent(interval=None)

        self._state: dict = {
            "cpu_percent": 0.0,
            "ram_percent": 0.0,
            "ram_used_gb": 0.0,
            "ram_total_gb": 0.0,
            "active_process": "unknown",
            "active_window_title": "",
            "uptime_minutes": 0,
            "timestamp": time.time(),
        }

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._collect_loop, daemon=True, name="SystemObserver")
        self._thread.start()
        print("SystemObserver: started.")

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=self._interval + 2)
        print("SystemObserver: stopped.")

    def get_state(self) -> dict:
        """Return a shallow copy of the current metrics snapshot."""
        with self._lock:
            return dict(self._state)

    # ------------------------------------------------------------------
    # Background loop
    # ------------------------------------------------------------------

    def _collect_loop(self):
        while self._running:
            try:
                self._collect_once()
            except Exception as e:
                print(f"SystemObserver: collection error: {e}")
            time.sleep(self._interval)

    def _collect_once(self):
        cpu = psutil.cpu_percent(interval=1)
        mem = psutil.virtual_memory()
        ram_pct = mem.percent
        ram_used = mem.used / (1024 ** 3)
        ram_total = mem.total / (1024 ** 3)

        boot_time = psutil.boot_time()
        uptime_min = int((time.time() - boot_time) / 60)

        proc_name, win_title = _get_active_window_info()

        with self._lock:
            self._state = {
                "cpu_percent": cpu,
                "ram_percent": ram_pct,
                "ram_used_gb": round(ram_used, 1),
                "ram_total_gb": round(ram_total, 1),
                "active_process": proc_name,
                "active_window_title": win_title,
                "uptime_minutes": uptime_min,
                "timestamp": time.time(),
            }
