# frontend/system_panel.py
import psutil
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QSizePolicy
from PyQt6.QtCore import Qt, QTimer


class SystemPanel(QWidget):
    """
    Fixed-height bottom bar showing CPU%, RAM%, mic status and Marvin status.
    Updates every 2 seconds via QTimer.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("system_panel")
        self.setFixedHeight(32)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        self._status_text = "idle"
        self._mic_active  = False

        self._build_ui()

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._refresh)
        self._timer.start(2000)
        self._refresh()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_marvin_status(self, status: str):
        """Update Marvin's status label (e.g. 'thinking', 'speaking', 'idle')."""
        self._status_text = status
        self._lbl_status.setText(f"● {status}")

    def set_mic_active(self, active: bool):
        self._mic_active = active
        self._lbl_mic.setText("🎙" if active else "🔇")

    # ------------------------------------------------------------------
    # Build UI
    # ------------------------------------------------------------------

    def _build_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 10, 0)
        layout.setSpacing(6)

        def _sep():
            s = QLabel("│")
            s.setObjectName("sys_sep")
            return s

        # CPU
        lbl_cpu_key = QLabel("CPU")
        lbl_cpu_key.setObjectName("sys_label")
        self._lbl_cpu = QLabel("–%")
        self._lbl_cpu.setObjectName("sys_value")

        # RAM
        lbl_ram_key = QLabel("RAM")
        lbl_ram_key.setObjectName("sys_label")
        self._lbl_ram = QLabel("–%")
        self._lbl_ram.setObjectName("sys_value")

        # Mic
        self._lbl_mic = QLabel("🔇")
        self._lbl_mic.setObjectName("sys_label")

        # Status
        self._lbl_status = QLabel("● idle")
        self._lbl_status.setObjectName("sys_label")
        self._lbl_status.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        for widget in (lbl_cpu_key, self._lbl_cpu, _sep(),
                       lbl_ram_key, self._lbl_ram, _sep(),
                       self._lbl_mic):
            layout.addWidget(widget)

        layout.addStretch()
        layout.addWidget(self._lbl_status)

    # ------------------------------------------------------------------
    # Refresh
    # ------------------------------------------------------------------

    def _refresh(self):
        cpu = psutil.cpu_percent(interval=None)
        ram = psutil.virtual_memory().percent

        self._lbl_cpu.setText(f"{cpu:.0f}%")
        self._lbl_ram.setText(f"{ram:.0f}%")

        # Dynamic color via property (matched in QSS)
        self._set_warning(self._lbl_cpu, cpu >= 80, cpu >= 95)
        self._set_warning(self._lbl_ram, ram >= 85, ram >= 95)

    @staticmethod
    def _set_warning(label: QLabel, warning: bool, critical: bool):
        label.setProperty("warning",  "true" if warning and not critical else "false")
        label.setProperty("critical", "true" if critical else "false")
        label.style().unpolish(label)
        label.style().polish(label)
