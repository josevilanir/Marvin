import sys
import threading

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QLabel, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QSizePolicy, QTabWidget, QScrollArea, QFrame, QSpacerItem,
)
from PySide6.QtGui import QFont, QColor, QPalette, QFontDatabase
from PySide6.QtCore import Qt, QTimer, Signal, QObject, QThread

from app.voice_interface.speech_recognizer import SpeechRecognizer
from app.nlp.intent_processor import IntentProcessor
from main_controller import MainController
from app.voice_interface.speech_synthesizer import SpeechSynthesizer

# ── Palette ───────────────────────────────────────────────────────────────────
BG          = "#0b0b0b"
SURFACE     = "#141414"
CARD        = "#181818"
CARD_BORDER = "#252525"
TEXT        = "#e8e8e8"
TEXT_MUTED  = "#5a5a5a"
TEXT_DIM    = "#888"
ACCENT      = "#00e5ff"
GREEN       = "#00d97e"
PURPLE      = "#9d7fe0"
BLUE        = "#4f8ef7"
ORANGE      = "#f5a623"

_BASE_STYLE = f"""
    QMainWindow, QWidget {{ background: {BG}; color: {TEXT}; }}

    QTabWidget::pane {{
        border: 1px solid {CARD_BORDER};
        background: {BG};
    }}
    QTabWidget::tab-bar {{ alignment: left; }}
    QTabBar::tab {{
        background: {SURFACE};
        color: {TEXT_MUTED};
        padding: 8px 20px;
        border: none;
        font-size: 12px;
        letter-spacing: 1px;
        text-transform: uppercase;
    }}
    QTabBar::tab:selected {{
        background: {CARD};
        color: {ACCENT};
        border-bottom: 2px solid {ACCENT};
    }}
    QTabBar::tab:hover:!selected {{ color: {TEXT}; background: #1c1c1c; }}

    QScrollArea {{ border: none; background: transparent; }}
    QScrollBar:vertical {{
        background: {SURFACE};
        width: 6px;
        border: none;
    }}
    QScrollBar::handle:vertical {{
        background: #333;
        border-radius: 3px;
        min-height: 30px;
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
"""


# ── RecognizerWorker ──────────────────────────────────────────────────────────

class RecognizerWorker(QObject):
    recognized    = Signal(str)
    status_update = Signal(str)

    def __init__(self, main_controller):
        super().__init__()
        self.running    = False
        self.recognizer = SpeechRecognizer()
        self.processor  = IntentProcessor(main_controller)

    def listen_loop(self):
        self.running = True
        while self.running:
            ativado = self.recognizer.listen_for_activation()
            if ativado:
                self.status_update.emit("Estou ouvindo...")
                frase = self.recognizer.recognize_once()
                if frase:
                    self.recognized.emit(frase)
                    resposta = self.processor.process(frase)
                    self.status_update.emit(resposta)

    def stop_listening(self):
        self.running = False


# ── Widgets for the Apps tab ──────────────────────────────────────────────────

class TypeBadge(QLabel):
    """Small colored pill showing 'cli' or 'uri'."""
    _COLORS = {
        "cli": (f"#0f2a1e", GREEN),
        "uri": (f"#1c1030", PURPLE),
    }

    def __init__(self, cap_type: str, parent=None):
        super().__init__(cap_type.upper(), parent)
        bg, fg = self._COLORS.get(cap_type.lower(), ("#222", TEXT_MUTED))
        self.setStyleSheet(f"""
            background: {bg};
            color: {fg};
            border: 1px solid {fg}44;
            border-radius: 3px;
            padding: 1px 6px;
            font-size: 9px;
            font-family: 'Consolas', 'Courier New', monospace;
            letter-spacing: 1px;
        """)
        self.setFixedHeight(16)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)


class DetectBadge(QLabel):
    """Shows 'via cli' or 'via sistema'."""
    def __init__(self, detected_by: str, parent=None):
        label = f"via {detected_by}"
        super().__init__(label, parent)
        self.setStyleSheet(f"""
            color: {TEXT_MUTED};
            font-size: 10px;
            font-family: 'Consolas', 'Courier New', monospace;
        """)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)


class CapabilityRow(QWidget):
    """One row inside an app card: tool_name + type badge + description."""

    def __init__(self, cap: dict, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background: transparent;")

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 6, 0, 6)
        root.setSpacing(3)

        # ── top row: tool name + type badge ──
        top = QHBoxLayout()
        top.setContentsMargins(0, 0, 0, 0)
        top.setSpacing(8)

        name = QLabel(cap["tool_name"])
        name.setStyleSheet(f"""
            color: {ACCENT};
            font-family: 'Consolas', 'Courier New', monospace;
            font-size: 12px;
        """)
        top.addWidget(name)
        top.addWidget(TypeBadge(cap["type"]))

        # params hint
        if cap["params"]:
            param_names = ", ".join(p["name"] for p in cap["params"])
            ph = QLabel(f"({param_names})")
            ph.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 10px; font-family: 'Consolas', monospace;")
            top.addWidget(ph)

        top.addStretch()
        root.addLayout(top)

        # ── description ──
        desc = QLabel(cap["description"])
        desc.setStyleSheet(f"color: {TEXT_DIM}; font-size: 11px;")
        desc.setWordWrap(True)
        root.addWidget(desc)

        # ── template ──
        if cap.get("template"):
            tmpl = QLabel(cap["template"])
            tmpl.setStyleSheet(f"""
                color: {TEXT_MUTED};
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 10px;
                background: #0f0f0f;
                border-radius: 3px;
                padding: 2px 6px;
            """)
            tmpl.setWordWrap(True)
            root.addWidget(tmpl)


class AppCard(QFrame):
    """Card widget displaying one app and all its capabilities."""

    def __init__(self, app_data: dict, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            QFrame {{
                background: {CARD};
                border: 1px solid {CARD_BORDER};
                border-radius: 8px;
            }}
        """)

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 14, 16, 14)
        root.setSpacing(0)

        # ── header ──────────────────────────────────────────────────────────
        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 10)
        header.setSpacing(10)

        dot = QLabel("●")
        dot.setStyleSheet(f"color: {GREEN}; font-size: 10px;")
        dot.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        header.addWidget(dot)

        app_name = QLabel(app_data["display_name"])
        app_name.setStyleSheet(f"color: {TEXT}; font-size: 14px; font-weight: 600;")
        header.addWidget(app_name)

        header.addWidget(DetectBadge(app_data["detected_by"]))
        header.addStretch()

        cap_count = QLabel(f"{len(app_data['capabilities'])} ações")
        cap_count.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 10px;")
        header.addWidget(cap_count)

        root.addLayout(header)

        # ── divider ──────────────────────────────────────────────────────────
        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setStyleSheet(f"background: {CARD_BORDER}; max-height: 1px; border: none;")
        root.addWidget(divider)

        # ── capabilities ─────────────────────────────────────────────────────
        for i, cap in enumerate(app_data["capabilities"]):
            row = CapabilityRow(cap)
            root.addWidget(row)
            if i < len(app_data["capabilities"]) - 1:
                sep = QFrame()
                sep.setFrameShape(QFrame.HLine)
                sep.setStyleSheet(f"background: #1f1f1f; max-height: 1px; border: none;")
                root.addWidget(sep)


# ── Apps tab ──────────────────────────────────────────────────────────────────

class AppsTab(QWidget):
    def __init__(self, main_controller, parent=None):
        super().__init__(parent)
        self._controller = main_controller
        self._cards: list[AppCard] = []

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(12)

        # ── toolbar ──
        toolbar = QHBoxLayout()

        self._summary = QLabel("Carregando apps...")
        self._summary.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px;")
        toolbar.addWidget(self._summary)
        toolbar.addStretch()

        self._btn_refresh = QPushButton("↻  Atualizar")
        self._btn_refresh.setStyleSheet(f"""
            QPushButton {{
                background: {SURFACE};
                color: {ACCENT};
                border: 1px solid {ACCENT}44;
                border-radius: 5px;
                padding: 4px 14px;
                font-size: 11px;
            }}
            QPushButton:hover {{ background: #1e2a2a; }}
            QPushButton:pressed {{ background: #0a1a1a; }}
        """)
        self._btn_refresh.setCursor(Qt.PointingHandCursor)
        self._btn_refresh.clicked.connect(self._refresh)
        toolbar.addWidget(self._btn_refresh)

        root.addLayout(toolbar)

        # ── scroll area ──
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self._cards_widget = QWidget()
        self._cards_widget.setStyleSheet("background: transparent;")
        self._cards_layout = QVBoxLayout(self._cards_widget)
        self._cards_layout.setContentsMargins(0, 0, 8, 0)
        self._cards_layout.setSpacing(10)
        self._cards_layout.addStretch()

        self._scroll.setWidget(self._cards_widget)
        root.addWidget(self._scroll)

        # Defer population until after GUI is shown
        QTimer.singleShot(100, self._populate)

    def _populate(self):
        svc = getattr(self._controller, "app_capability_service", None)
        if svc is None:
            self._summary.setText("AppCapabilityService não disponível.")
            return

        profiles = svc.get_active_profiles()
        self._rebuild_cards(profiles)

    def _refresh(self):
        self._btn_refresh.setEnabled(False)
        self._btn_refresh.setText("...")
        svc = getattr(self._controller, "app_capability_service", None)
        if svc:
            svc.refresh()
            self._populate()
        self._btn_refresh.setEnabled(True)
        self._btn_refresh.setText("↻  Atualizar")

    def _rebuild_cards(self, profiles: list[dict]):
        # Clear old cards (keep stretch at end)
        while self._cards_layout.count() > 1:
            item = self._cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not profiles:
            empty = QLabel("Nenhum app do catálogo detectado.")
            empty.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 13px;")
            empty.setAlignment(Qt.AlignCenter)
            self._cards_layout.insertWidget(0, empty)
            self._summary.setText("0 apps registrados")
            return

        total_caps = sum(len(p["capabilities"]) for p in profiles)
        self._summary.setText(
            f"{len(profiles)} apps detectados  ·  {total_caps} ações disponíveis"
        )

        for i, app_data in enumerate(profiles):
            card = AppCard(app_data)
            self._cards_layout.insertWidget(i, card)


# ── Main tab (voice interface) ────────────────────────────────────────────────

class MainTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 30, 24, 24)
        layout.setSpacing(0)

        # ── title ──
        title = QLabel("MARVIN")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(f"""
            color: {ACCENT};
            font-size: 26px;
            font-weight: 700;
            letter-spacing: 8px;
            font-family: 'Consolas', 'Courier New', monospace;
        """)
        layout.addWidget(title)
        layout.addSpacing(4)

        subtitle = QLabel("assistente pessoal")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 10px; letter-spacing: 3px;")
        layout.addWidget(subtitle)
        layout.addSpacing(32)

        # ── status ──
        self.label_status = QLabel("Aguardando ativação...")
        self.label_status.setAlignment(Qt.AlignCenter)
        self.label_status.setStyleSheet(f"color: {TEXT}; font-size: 14px;")
        layout.addWidget(self.label_status)
        layout.addSpacing(16)

        # ── transcription ──
        self.label_transcription = QLabel("")
        self.label_transcription.setAlignment(Qt.AlignCenter)
        self.label_transcription.setWordWrap(True)
        self.label_transcription.setStyleSheet(f"""
            color: {TEXT_DIM};
            font-size: 12px;
            padding: 12px;
            background: {SURFACE};
            border-radius: 8px;
            min-height: 60px;
        """)
        self.label_transcription.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.label_transcription)

        layout.addStretch()

        # ── mic button ──
        self.button_toggle = QPushButton("Ativar Microfone")
        self.button_toggle.setStyleSheet(f"""
            QPushButton {{
                background: {SURFACE};
                color: {TEXT};
                border: 1px solid {CARD_BORDER};
                border-radius: 8px;
                padding: 12px;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background: #1e1e1e;
                border-color: {ACCENT}66;
                color: {ACCENT};
            }}
            QPushButton:pressed {{ background: #141414; }}
            QPushButton[active="true"] {{
                background: #0f2020;
                border-color: {GREEN};
                color: {GREEN};
            }}
        """)
        self.button_toggle.setCursor(Qt.PointingHandCursor)
        layout.addWidget(self.button_toggle)


# ── MarvinGUI ─────────────────────────────────────────────────────────────────

class MarvinGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Marvin")
        self.setMinimumSize(460, 560)
        self.resize(460, 620)
        self.setStyleSheet(_BASE_STYLE)

        # Shared MainController — used by both the voice worker and the apps tab
        self.main_controller = MainController()

        # ── Tabs ──
        self._tabs = QTabWidget()
        self._tabs.setDocumentMode(True)
        self.setCentralWidget(self._tabs)

        self._main_tab = MainTab()
        self._apps_tab = AppsTab(self.main_controller)

        self._tabs.addTab(self._main_tab, "Marvin")
        self._tabs.addTab(self._apps_tab, "Apps")

        # ── Voice worker ──
        self.listening = False
        self.worker = RecognizerWorker(self.main_controller)
        self.worker.recognized.connect(self._main_tab.label_transcription.setText)
        self.worker.status_update.connect(self._main_tab.label_status.setText)
        self._main_tab.button_toggle.clicked.connect(self.toggle_microphone)

    def toggle_microphone(self):
        self.listening = not self.listening
        btn = self._main_tab.button_toggle
        if self.listening:
            self._main_tab.label_status.setText("Estou ouvindo...")
            btn.setText("Desativar Microfone")
            btn.setProperty("active", "true")
            btn.style().unpolish(btn)
            btn.style().polish(btn)
            self.listen_thread = threading.Thread(target=self.worker.listen_loop, daemon=True)
            self.listen_thread.start()
        else:
            self._main_tab.label_status.setText("Aguardando ativação...")
            btn.setText("Ativar Microfone")
            btn.setProperty("active", "false")
            btn.style().unpolish(btn)
            btn.style().polish(btn)
            self._main_tab.label_transcription.setText("")
            self.worker.stop_listening()


def run_gui():
    app = QApplication(sys.argv)
    window = MarvinGUI()
    window.show()
    sys.exit(app.exec())
