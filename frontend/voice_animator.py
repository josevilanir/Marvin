# frontend/voice_animator.py
import math
import random
from PyQt6.QtWidgets import QWidget, QSizePolicy
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPainter, QColor, QPen

_BAR_COUNT = 5
_FPS = 30
_COLORS = {
    "idle":      QColor(0x00, 0x88, 0xaa, 120),   # muted cyan
    "speaking":  QColor(0x00, 0xd4, 0xff, 255),    # bright cyan
    "listening": QColor(0x00, 0xff, 0x88, 220),    # green
}
_BORDER_COLORS = {
    "idle":      QColor(0x00, 0x88, 0xaa, 60),
    "speaking":  QColor(0x00, 0xd4, 0xff, 180),
    "listening": QColor(0x00, 0xff, 0x88, 140),
}

# Amplitude ranges per state (min, max) in pixels
_AMPLITUDES = {
    "idle":      (4,  10),
    "speaking":  (14, 38),
    "listening": (10, 26),
}

# Animation speed (phase increment per tick)
_SPEEDS = {
    "idle":     0.06,
    "speaking": 0.18,
    "listening":0.12,
}


class VoiceAnimator(QWidget):
    """
    Five vertical bars that animate to represent voice activity.
    States: "idle" | "speaking" | "listening"
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(60)
        self.setMinimumWidth(180)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self._state = "idle"
        self._phases = [i * (math.pi * 2 / _BAR_COUNT) for i in range(_BAR_COUNT)]
        self._targets = [6.0] * _BAR_COUNT   # current target heights
        self._heights = [6.0] * _BAR_COUNT   # smooth current heights

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(1000 // _FPS)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_state(self, state: str):
        """Set animation state: 'idle', 'speaking', or 'listening'."""
        if state in _AMPLITUDES:
            self._state = state

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _tick(self):
        speed = _SPEEDS[self._state]
        lo, hi = _AMPLITUDES[self._state]

        for i in range(_BAR_COUNT):
            self._phases[i] += speed + random.uniform(-0.02, 0.02)
            base = (math.sin(self._phases[i]) + 1) / 2   # 0..1
            noise = random.uniform(-0.15, 0.15)
            self._targets[i] = lo + (hi - lo) * max(0.0, min(1.0, base + noise))
            # Smooth lerp toward target
            self._heights[i] += (self._targets[i] - self._heights[i]) * 0.35

        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()
        bar_w = 4
        total_bars_w = _BAR_COUNT * bar_w
        spacing = (w - total_bars_w) / (_BAR_COUNT + 1)

        color = _COLORS[self._state]
        glow  = _BORDER_COLORS[self._state]

        for i in range(_BAR_COUNT):
            bar_h = max(4, self._heights[i])
            x = int(spacing + i * (bar_w + spacing))
            y = int((h - bar_h) / 2)

            # Glow shadow (wider, translucent)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(glow)
            painter.drawRoundedRect(x - 2, y - 2, bar_w + 4, int(bar_h) + 4, 4, 4)

            # Main bar
            painter.setBrush(color)
            painter.drawRoundedRect(x, y, bar_w, int(bar_h), 2, 2)

        painter.end()
