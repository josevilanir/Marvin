# frontend/chat_panel.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea,
    QLabel, QLineEdit, QPushButton, QSizePolicy, QFrame,
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal


class _MessageBubble(QWidget):
    """Single chat message bubble."""

    def __init__(self, sender: str, text: str, parent=None):
        super().__init__(parent)
        is_user = sender == "user"

        outer = QHBoxLayout(self)
        outer.setContentsMargins(8, 3, 8, 3)

        bubble = QWidget()
        bubble.setObjectName("msg_user" if is_user else "msg_marvin")
        bubble.setMaximumWidth(280)

        inner = QVBoxLayout(bubble)
        inner.setContentsMargins(10, 6, 10, 6)
        inner.setSpacing(2)

        lbl_sender = QLabel("Você" if is_user else "Marvin")
        lbl_sender.setObjectName("msg_sender")

        lbl_text = QLabel(text)
        lbl_text.setObjectName("msg_user_text" if is_user else "msg_marvin_text")
        lbl_text.setWordWrap(True)
        lbl_text.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)

        inner.addWidget(lbl_sender)
        inner.addWidget(lbl_text)

        if is_user:
            outer.addStretch()
            outer.addWidget(bubble)
        else:
            outer.addWidget(bubble)
            outer.addStretch()


class ChatPanel(QWidget):
    """
    Scrollable chat history + input bar.
    Signals:
        message_submitted(str) — emitted when user sends a message
        mic_toggled(bool)      — emitted when mic button is pressed (True = active)
    """

    message_submitted = pyqtSignal(str)
    mic_toggled       = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._mic_active = False
        self._build_ui()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def add_message(self, sender: str, text: str):
        """Add a message bubble. sender: 'user' | 'marvin'"""
        bubble = _MessageBubble(sender, text)
        self._messages_layout.addWidget(bubble)
        # Auto-scroll after layout settles
        QTimer.singleShot(50, self._scroll_to_bottom)

    def get_input(self) -> str:
        """Return and clear the input field."""
        text = self._input.text().strip()
        self._input.clear()
        return text

    def set_input_enabled(self, enabled: bool):
        self._input.setEnabled(enabled)
        self._btn_send.setEnabled(enabled)

    # ------------------------------------------------------------------
    # Build UI
    # ------------------------------------------------------------------

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Scroll area ──────────────────────────────────────────────
        self._scroll = QScrollArea()
        self._scroll.setObjectName("chat_scroll")
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)

        self._messages_widget = QWidget()
        self._messages_widget.setObjectName("chat_content")
        self._messages_layout = QVBoxLayout(self._messages_widget)
        self._messages_layout.setContentsMargins(0, 8, 0, 8)
        self._messages_layout.setSpacing(4)
        self._messages_layout.addStretch()   # pushes messages to bottom initially

        self._scroll.setWidget(self._messages_widget)

        # ── Input bar ────────────────────────────────────────────────
        input_bar = QWidget()
        input_bar.setObjectName("input_bar")
        input_bar.setFixedHeight(52)

        bar_layout = QHBoxLayout(input_bar)
        bar_layout.setContentsMargins(10, 8, 10, 8)
        bar_layout.setSpacing(8)

        self._input = QLineEdit()
        self._input.setObjectName("chat_input")
        self._input.setPlaceholderText("Digite ou use o microfone…")
        self._input.returnPressed.connect(self._on_send)

        self._btn_mic = QPushButton("🎙")
        self._btn_mic.setObjectName("btn_mic")
        self._btn_mic.setFixedSize(36, 36)
        self._btn_mic.setProperty("active", "false")
        self._btn_mic.clicked.connect(self._on_mic_clicked)

        self._btn_send = QPushButton("Enviar")
        self._btn_send.setObjectName("btn_send")
        self._btn_send.setFixedWidth(72)
        self._btn_send.clicked.connect(self._on_send)

        bar_layout.addWidget(self._btn_mic)
        bar_layout.addWidget(self._input)
        bar_layout.addWidget(self._btn_send)

        layout.addWidget(self._scroll)
        layout.addWidget(input_bar)

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _on_mic_clicked(self):
        self._mic_active = not self._mic_active
        active_str = "true" if self._mic_active else "false"
        self._btn_mic.setProperty("active", active_str)
        self._btn_mic.style().unpolish(self._btn_mic)
        self._btn_mic.style().polish(self._btn_mic)
        self.mic_toggled.emit(self._mic_active)

    def set_mic_state(self, active: bool):
        """Called externally to sync mic button state."""
        self._mic_active = active
        active_str = "true" if active else "false"
        self._btn_mic.setProperty("active", active_str)
        self._btn_mic.style().unpolish(self._btn_mic)
        self._btn_mic.style().polish(self._btn_mic)

    def _on_send(self):
        text = self._input.text().strip()
        if text:
            self._input.clear()
            self.message_submitted.emit(text)

    def _scroll_to_bottom(self):
        bar = self._scroll.verticalScrollBar()
        bar.setValue(bar.maximum())
