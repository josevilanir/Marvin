# frontend/marvin_widget.py
import os
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QSystemTrayIcon, QMenu, QApplication, QStackedWidget,
)
from PyQt6.QtCore import Qt, QPoint, pyqtSlot, pyqtSignal
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QFont

from frontend.voice_animator import VoiceAnimator
from frontend.chat_panel import ChatPanel
from frontend.system_panel import SystemPanel
from frontend.apps_panel import AppsPanel

_WINDOW_W = 380
_WINDOW_H = 600
_HEADER_H = 48
_ANIM_H   = 70


def _make_tray_icon() -> QIcon:
    """Generate a simple 32x32 cyan 'M' icon for the system tray."""
    px = QPixmap(32, 32)
    px.fill(QColor(0x0d, 0x0d, 0x0f))
    p = QPainter(px)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setPen(QColor(0x00, 0xd4, 0xff))
    font = QFont("Segoe UI", 18, QFont.Weight.Bold)
    p.setFont(font)
    p.drawText(px.rect(), Qt.AlignmentFlag.AlignCenter, "M")
    p.end()
    return QIcon(px)


class _Header(QWidget):
    """Draggable header with title, status dot, minimize and close buttons."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("header")
        self.setFixedHeight(_HEADER_H)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 0, 8, 0)
        layout.setSpacing(6)

        self._dot = QLabel("●")
        self._dot.setObjectName("status_dot")
        self._dot.setStyleSheet("color: #444455;")

        lbl_title = QLabel("MARVIN")
        lbl_title.setObjectName("title")

        self._lbl_sub = QLabel("assistente")
        self._lbl_sub.setObjectName("subtitle")

        btn_min = QPushButton("−")
        btn_min.setObjectName("btn_minimize")
        btn_min.setFixedSize(28, 28)
        btn_min.clicked.connect(self._on_minimize)

        btn_close = QPushButton("×")
        btn_close.setObjectName("btn_close")
        btn_close.setFixedSize(28, 28)
        btn_close.clicked.connect(self._on_close)

        layout.addWidget(self._dot)
        layout.addWidget(lbl_title)
        layout.addWidget(self._lbl_sub)
        layout.addStretch()
        layout.addWidget(btn_min)
        layout.addWidget(btn_close)

        # Dragging state
        self._drag_pos: QPoint | None = None

    # -- Status dot ---------------------------------------------------

    def set_status(self, status: str):
        colors = {
            "idle":      "#444455",
            "listening": "#00ff88",
            "thinking":  "#ffaa00",
            "speaking":  "#00d4ff",
        }
        color = colors.get(status, "#444455")
        self._dot.setStyleSheet(f"color: {color};")
        self._lbl_sub.setText(status)

    # -- Window controls ----------------------------------------------

    def _on_minimize(self):
        win: MarvinWidget = self.window()
        win.toggle_collapse()

    def _on_close(self):
        win: MarvinWidget = self.window()
        win.hide()

    # -- Dragging -----------------------------------------------------

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.window().frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if self._drag_pos and event.buttons() & Qt.MouseButton.LeftButton:
            self.window().move(event.globalPosition().toPoint() - self._drag_pos)

    def mouseReleaseEvent(self, event):
        self._drag_pos = None


class _NavBar(QWidget):
    """
    Thin two-button bar for switching between Chat and Apps panels.
    Emits tab_changed(int) with the index of the selected tab.
    """
    tab_changed = pyqtSignal(int)

    _LABELS = ["Chat", "Apps"]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("nav_bar")
        self.setFixedHeight(30)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 10, 0)
        layout.setSpacing(4)

        self._btns: list[QPushButton] = []
        for i, label in enumerate(self._LABELS):
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setObjectName("nav_btn")
            btn.setProperty("active", "true" if i == 0 else "false")
            btn.setFixedHeight(26)
            btn.setStyleSheet(self._btn_style(i == 0))
            btn.clicked.connect(lambda _, idx=i: self._select(idx))
            layout.addWidget(btn)
            self._btns.append(btn)

        layout.addStretch()

    @staticmethod
    def _btn_style(active: bool) -> str:
        accent = "#00d4ff"
        if active:
            return f"""
                QPushButton {{
                    background: #0d1c22;
                    color: {accent};
                    border: none;
                    border-bottom: 2px solid {accent};
                    border-radius: 0px;
                    padding: 0 14px;
                    font-size: 11px;
                    letter-spacing: 1px;
                }}
            """
        return """
            QPushButton {
                background: transparent;
                color: #44445a;
                border: none;
                border-bottom: 2px solid transparent;
                border-radius: 0px;
                padding: 0 14px;
                font-size: 11px;
                letter-spacing: 1px;
            }
            QPushButton:hover { color: #888899; }
        """

    def _select(self, idx: int):
        for i, btn in enumerate(self._btns):
            btn.setStyleSheet(self._btn_style(i == idx))
        self.tab_changed.emit(idx)


class MarvinWidget(QMainWindow):
    """
    Main always-on-top floating HUD window.
    Collapsed: shows only the header (48px).
    Expanded:  full 380×600 layout.
    """

    def __init__(self, bridge=None):
        super().__init__()
        self._bridge = bridge
        self._collapsed = False
        self._expanded_height = _WINDOW_H
        self._setup_window()
        self._build_ui()
        self._setup_tray()
        self._position_bottom_right()

        if bridge:
            self._connect_bridge()

    # ------------------------------------------------------------------
    # Window setup
    # ------------------------------------------------------------------

    def _setup_window(self):
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool                  # keeps out of taskbar
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.resize(_WINDOW_W, _WINDOW_H)

        # Load stylesheet
        qss_path = os.path.join(os.path.dirname(__file__), "assets", "style.qss")
        if os.path.exists(qss_path):
            with open(qss_path, "r", encoding="utf-8") as f:
                self.setStyleSheet(f.read())

    def _build_ui(self):
        central = QWidget()
        central.setObjectName("central")
        self.setCentralWidget(central)

        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Header
        self._header = _Header(self)
        main_layout.addWidget(self._header)

        # Animator
        anim_container = QWidget()
        anim_container.setFixedHeight(_ANIM_H)
        anim_container.setObjectName("central")
        anim_layout = QHBoxLayout(anim_container)
        anim_layout.setContentsMargins(16, 4, 16, 4)
        self._animator = VoiceAnimator()
        anim_layout.addWidget(self._animator)
        main_layout.addWidget(anim_container)

        # Nav bar (Chat | Apps)
        self._nav = _NavBar()
        self._nav.tab_changed.connect(self._on_nav_changed)
        main_layout.addWidget(self._nav)

        # Stacked content: index 0 = Chat, index 1 = Apps
        self._stack = QStackedWidget()
        self._stack.setStyleSheet("background: #0d0d0f;")

        self._chat = ChatPanel()
        self._chat.message_submitted.connect(self._on_user_text_input)
        self._chat.mic_toggled.connect(self._on_mic_toggled)
        self._stack.addWidget(self._chat)      # index 0

        self._apps = AppsPanel()
        self._stack.addWidget(self._apps)      # index 1

        main_layout.addWidget(self._stack, stretch=1)

        # System panel
        self._sys_panel = SystemPanel()
        main_layout.addWidget(self._sys_panel)

    def _setup_tray(self):
        icon = _make_tray_icon()
        self._tray = QSystemTrayIcon(icon, self)
        menu = QMenu()
        menu.addAction("Abrir",  self.show)
        menu.addSeparator()
        menu.addAction("Sair", QApplication.instance().quit)
        self._tray.setContextMenu(menu)
        self._tray.activated.connect(self._on_tray_activated)
        self._tray.show()

    def _position_bottom_right(self):
        screen = QApplication.primaryScreen().availableGeometry()
        x = screen.right()  - _WINDOW_W - 20
        y = screen.bottom() - _WINDOW_H - 20
        self.move(x, y)

    # ------------------------------------------------------------------
    # Bridge connection
    # ------------------------------------------------------------------

    def _connect_bridge(self):
        b = self._bridge
        if hasattr(b, "marvin_response"):
            b.marvin_response.connect(self._on_marvin_response)
        if hasattr(b, "marvin_speaking_start"):
            b.marvin_speaking_start.connect(self._on_speaking_start)
        if hasattr(b, "marvin_speaking_end"):
            b.marvin_speaking_end.connect(self._on_speaking_end)
        if hasattr(b, "status_changed"):
            b.status_changed.connect(self._on_status_changed)
        if hasattr(b, "proactive_message"):
            # Proactive messages show in chat like regular Marvin messages
            b.proactive_message.connect(self._on_marvin_response)

    # ------------------------------------------------------------------
    # Public slots
    # ------------------------------------------------------------------

    @pyqtSlot(str)
    def _on_marvin_response(self, text: str):
        self._chat.add_message("marvin", text)

    @pyqtSlot()
    def _on_speaking_start(self):
        self._animator.set_state("speaking")
        self._header.set_status("speaking")
        self._sys_panel.set_marvin_status("speaking")

    @pyqtSlot()
    def _on_speaking_end(self):
        self._animator.set_state("idle")
        self._header.set_status("idle")
        self._sys_panel.set_marvin_status("idle")

    @pyqtSlot(str)
    def _on_status_changed(self, status: str):
        self._header.set_status(status)
        self._sys_panel.set_marvin_status(status)
        state_map = {"listening": "listening", "thinking": "idle", "speaking": "speaking"}
        self._animator.set_state(state_map.get(status, "idle"))

    @pyqtSlot(str)
    def _on_user_text_input(self, text: str):
        self._chat.add_message("user", text)
        self._header.set_status("thinking")
        self._animator.set_state("listening")
        if self._bridge and hasattr(self._bridge, "submit_text"):
            self._bridge.submit_text(text)

    # ------------------------------------------------------------------
    # Nav
    # ------------------------------------------------------------------

    @pyqtSlot(int)
    def _on_nav_changed(self, idx: int):
        self._stack.setCurrentIndex(idx)

    # ------------------------------------------------------------------
    # Mic toggle
    # ------------------------------------------------------------------

    def _on_mic_toggled(self, active: bool):
        self._sys_panel.set_mic_active(active)
        if self._bridge and hasattr(self._bridge, "set_mic_active"):
            self._bridge.set_mic_active(active)
        state = "listening" if active else "idle"
        self._animator.set_state(state)
        self._header.set_status(state)

    # ------------------------------------------------------------------
    # Collapse / expand
    # ------------------------------------------------------------------

    def toggle_collapse(self):
        if self._collapsed:
            self.setFixedHeight(_WINDOW_H)
            self._collapsed = False
        else:
            self.setFixedHeight(_HEADER_H)
            self._collapsed = True

    # ------------------------------------------------------------------
    # Tray
    # ------------------------------------------------------------------

    def _on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show()
            self.activateWindow()

    def closeEvent(self, event):
        """Graceful shutdown: stop background threads before exiting."""
        if self._bridge and hasattr(self._bridge, "stop"):
            self._bridge.stop()
        event.accept()
