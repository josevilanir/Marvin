# main.py — Entry point do Marvin v2
import sys
import os

try:
    from PyQt6.QtWidgets import QApplication
except ImportError:
    print("ERRO: PyQt6 não instalado. Execute: pip install PyQt6")
    sys.exit(1)

# Adiciona o backend ao path antes de qualquer import do frontend
_backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend")
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

from frontend.marvin_widget import MarvinWidget
from frontend.bridge import MarvinBridge


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Marvin")
    app.setQuitOnLastWindowClosed(False)  # mantém vivo no system tray

    bridge = MarvinBridge()
    widget = MarvinWidget(bridge)
    widget.show()

    bridge.start()   # inicia worker thread + saudação inicial

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
