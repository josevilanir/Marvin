# frontend/apps_panel.py
"""
AppsPanel — scrollable view of apps detected by AppCapabilityService.
Uses pyqtSignal for thread-safe UI updates from the background loader.
"""
import threading

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea,
    QLabel, QPushButton, QFrame, QSizePolicy,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

# ── Palette ────────────────────────────────────────────────────────────────
_BG     = "#0d0d0f"
_SURF   = "#12121a"
_CARD   = "#16161e"
_BORDER = "#1f1f2e"
_TEXT   = "#dde1f0"
_MUTED  = "#555570"
_DIM    = "#888aaa"
_ACCENT = "#00d4ff"
_GREEN  = "#00e87c"
_PURPLE = "#a855f7"
_MONO   = "Consolas, 'Courier New', monospace"


# ── Sub-widgets ────────────────────────────────────────────────────────────

class _Badge(QLabel):
    _STYLES = {
        "cli": f"background:#0c2318; color:#00e87c; border:1px solid #00e87c44;",
        "uri": f"background:#1a0a2e; color:#a855f7; border:1px solid #a855f744;",
    }

    def __init__(self, kind: str, parent=None):
        super().__init__(kind.upper(), parent)
        style = self._STYLES.get(kind.lower(),
            f"background:#1a1a1a; color:#555570; border:1px solid #55557044;")
        self.setStyleSheet(f"""
            {style}
            border-radius: 3px; padding: 1px 5px;
            font-size: 9px; font-family: {_MONO}; letter-spacing: 1px;
        """)
        self.setFixedHeight(15)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)


class _CapRow(QWidget):
    def __init__(self, cap: dict, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: transparent;")

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 8, 0, 8)
        root.setSpacing(3)

        # tool_name  [TYPE]  {params}
        top = QHBoxLayout()
        top.setContentsMargins(0, 0, 0, 0)
        top.setSpacing(7)

        name = QLabel(cap["tool_name"])
        name.setStyleSheet(f"color:{_ACCENT}; font-family:{_MONO}; font-size:12px;")
        top.addWidget(name)
        top.addWidget(_Badge(cap["type"]))

        if cap.get("params"):
            hint = "  " + "  ".join(f"{{{p['name']}}}" for p in cap["params"])
            lbl = QLabel(hint)
            lbl.setStyleSheet(f"color:{_MUTED}; font-size:10px; font-family:{_MONO};")
            top.addWidget(lbl)
        top.addStretch()
        root.addLayout(top)

        # description
        desc = QLabel(cap["description"])
        desc.setStyleSheet(f"color:{_DIM}; font-size:11px;")
        desc.setWordWrap(True)
        root.addWidget(desc)

        # command / uri template
        if cap.get("template"):
            tmpl = QLabel(cap["template"])
            tmpl.setStyleSheet(f"""
                color:{_MUTED}; font-family:{_MONO}; font-size:10px;
                background:#0a0a0f; border-radius:3px; padding:2px 7px;
            """)
            tmpl.setWordWrap(True)
            root.addWidget(tmpl)


class _AppCard(QFrame):
    def __init__(self, app: dict, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            QFrame {{ background:{_CARD}; border:1px solid {_BORDER}; border-radius:8px; }}
        """)

        root = QVBoxLayout(self)
        root.setContentsMargins(14, 12, 14, 12)
        root.setSpacing(0)

        # header
        hdr = QHBoxLayout()
        hdr.setContentsMargins(0, 0, 0, 10)
        hdr.setSpacing(8)

        dot = QLabel("●")
        dot.setStyleSheet(f"color:{_GREEN}; font-size:9px;")
        dot.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        hdr.addWidget(dot)

        lbl_name = QLabel(app["display_name"])
        lbl_name.setStyleSheet(f"color:{_TEXT}; font-size:13px; font-weight:600;")
        hdr.addWidget(lbl_name)

        lbl_det = QLabel(f"via {app['detected_by']}")
        lbl_det.setStyleSheet(f"color:{_MUTED}; font-size:10px; font-family:{_MONO};")
        hdr.addWidget(lbl_det)

        hdr.addStretch()

        n = len(app["capabilities"])
        lbl_n = QLabel(f"{n} {'ação' if n == 1 else 'ações'}")
        lbl_n.setStyleSheet(f"color:{_MUTED}; font-size:10px;")
        hdr.addWidget(lbl_n)
        root.addLayout(hdr)

        # divider
        div = QFrame()
        div.setFrameShape(QFrame.Shape.HLine)
        div.setStyleSheet(f"background:{_BORDER}; max-height:1px; border:none;")
        root.addWidget(div)

        # capabilities
        for i, cap in enumerate(app["capabilities"]):
            root.addWidget(_CapRow(cap))
            if i < len(app["capabilities"]) - 1:
                sep = QFrame()
                sep.setFrameShape(QFrame.Shape.HLine)
                sep.setStyleSheet("background:#1a1a22; max-height:1px; border:none;")
                root.addWidget(sep)


# ── Main panel ─────────────────────────────────────────────────────────────

class AppsPanel(QWidget):
    # Signals for thread-safe UI updates
    _data_ready    = pyqtSignal(list)
    _load_error    = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._loaded = False
        self.setStyleSheet(f"background:{_BG};")

        self._data_ready.connect(self._rebuild)
        self._load_error.connect(self._show_error)

        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 10, 12, 10)
        root.setSpacing(8)

        # toolbar
        bar = QHBoxLayout()
        bar.setContentsMargins(0, 0, 0, 0)

        self._lbl_summary = QLabel("Detectando apps instalados...")
        self._lbl_summary.setStyleSheet(f"color:{_MUTED}; font-size:10px;")
        bar.addWidget(self._lbl_summary)
        bar.addStretch()

        self._btn_refresh = QPushButton("↻")
        self._btn_refresh.setToolTip("Reescanear apps instalados")
        self._btn_refresh.setFixedSize(28, 24)
        self._btn_refresh.setStyleSheet(f"""
            QPushButton {{
                background:{_SURF}; color:{_ACCENT};
                border:1px solid {_ACCENT}33; border-radius:5px; font-size:13px;
            }}
            QPushButton:hover  {{ background:#1a2a2a; border-color:{_ACCENT}77; }}
            QPushButton:pressed {{ background:#0a1a1a; }}
            QPushButton:disabled {{ color:#333; border-color:#222; }}
        """)
        self._btn_refresh.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_refresh.clicked.connect(self._trigger_load)
        bar.addWidget(self._btn_refresh)

        root.addLayout(bar)

        # scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet(f"""
            QScrollArea {{ background:transparent; border:none; }}
            QScrollBar:vertical {{
                background:{_SURF}; width:5px; border:none;
            }}
            QScrollBar::handle:vertical {{
                background:#2a2a3a; border-radius:2px; min-height:24px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height:0; }}
        """)

        self._cards_widget = QWidget()
        self._cards_widget.setStyleSheet("background:transparent;")
        self._cards_layout = QVBoxLayout(self._cards_widget)
        self._cards_layout.setContentsMargins(0, 0, 6, 0)
        self._cards_layout.setSpacing(8)
        self._cards_layout.addStretch()

        scroll.setWidget(self._cards_widget)
        root.addWidget(scroll, stretch=1)

    # ── Loading ────────────────────────────────────────────────────────

    def showEvent(self, event):
        super().showEvent(event)
        if not self._loaded:
            self._trigger_load()

    def _trigger_load(self):
        self._loaded = True
        self._btn_refresh.setEnabled(False)
        self._lbl_summary.setText("Detectando apps instalados...")
        threading.Thread(target=self._load_worker, daemon=True).start()

    def _load_worker(self):
        """Runs in background thread. Emits signals to update UI safely."""
        try:
            from app.services.app_capability_service import AppCapabilityService
            svc = AppCapabilityService()
            profiles = svc.get_active_profiles()
            self._data_ready.emit(profiles)
        except Exception as exc:
            self._load_error.emit(str(exc))

    # ── Render (always called in main thread via signal) ───────────────

    def _rebuild(self, profiles: list):
        # clear all cards (keep the trailing stretch)
        while self._cards_layout.count() > 1:
            item = self._cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self._btn_refresh.setEnabled(True)

        if not profiles:
            lbl = QLabel("Nenhum app do catálogo detectado.")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet(f"color:{_MUTED}; font-size:12px;")
            self._cards_layout.insertWidget(0, lbl)
            self._lbl_summary.setText("0 apps detectados")
            return

        total = sum(len(p["capabilities"]) for p in profiles)
        self._lbl_summary.setText(
            f"{len(profiles)} apps detectados  ·  {total} ações disponíveis"
        )
        for i, app in enumerate(profiles):
            self._cards_layout.insertWidget(i, _AppCard(app))

    def _show_error(self, msg: str):
        self._btn_refresh.setEnabled(True)
        self._lbl_summary.setText("Erro ao carregar")
        lbl = QLabel(f"Erro: {msg}")
        lbl.setStyleSheet("color:#ff5555; font-size:11px;")
        lbl.setWordWrap(True)
        while self._cards_layout.count() > 1:
            item = self._cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._cards_layout.insertWidget(0, lbl)
