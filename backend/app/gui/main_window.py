from PySide6.QtWidgets import QApplication, QMainWindow, QLabel
import sys

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Marvin")
        self.setGeometry(100, 100, 400, 300)

        self.label = QLabel("Bem-vindo ao Marvin!", self)
        self.label.move(100, 130)

def run_gui():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
