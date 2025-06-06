import sys
import threading

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QLabel, QWidget, QVBoxLayout, QPushButton, QSizePolicy
)
from PySide6.QtGui import QFont, QColor, QPalette
from PySide6.QtCore import Qt, QTimer, Signal, QObject

from app.voice_interface.speech_recognizer import SpeechRecognizer
from app.nlp.intent_processor import IntentProcessor
from main_controller import MainController
from app.voice_interface.speech_synthesizer import SpeechSynthesizer


class RecognizerWorker(QObject):
    recognized = Signal(str)
    status_update = Signal(str)

    def __init__(self, main_controller):
        super().__init__()
        self.running = False
        self.recognizer = SpeechRecognizer()
        self.processor = IntentProcessor(main_controller)

    def listen_loop(self):
        self.running = True
        while self.running:
            ativado = self.recognizer.listen_for_activation()
            if ativado:
                self.status_update.emit("🦻 Estou ouvindo...")
                frase = self.recognizer.recognize_once()
                if frase:
                    self.recognized.emit(f"🗣️ {frase}")
                    resposta = self.processor.process(frase)
                    self.status_update.emit(f"🤖 {resposta}")

    def stop_listening(self):
        self.running = False


class MarvinGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Marvin")
        self.setFixedSize(400, 350)

        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(30, 30, 30))
        palette.setColor(QPalette.WindowText, Qt.white)
        self.setPalette(palette)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        self.label_title = QLabel("Bem-vindo ao Marvin")
        self.label_title.setAlignment(Qt.AlignCenter)
        self.label_title.setFont(QFont("Arial", 16, QFont.Bold))

        self.label_status = QLabel("🎙️ Aguardando ativação...")
        self.label_status.setAlignment(Qt.AlignCenter)
        self.label_status.setFont(QFont("Arial", 14))

        self.label_transcription = QLabel("")
        self.label_transcription.setAlignment(Qt.AlignCenter)
        self.label_transcription.setFont(QFont("Arial", 12))
        self.label_transcription.setWordWrap(True)
        self.label_transcription.setStyleSheet("color: lightgray;")
        self.label_transcription.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.label_transcription.setStyleSheet("""
            color: lightgray;
            padding: 10px;
            margin: 10px;
            border: none;
            """)

        self.button_toggle = QPushButton("Ativar Microfone")
        self.button_toggle.setFont(QFont("Arial", 11))
        self.button_toggle.clicked.connect(self.toggle_microphone)

        self.layout.addWidget(self.label_title)
        self.layout.addSpacing(10)
        self.layout.addWidget(self.label_status)
        self.layout.addSpacing(10)
        self.layout.addWidget(self.label_transcription)
        self.layout.addStretch()
        self.layout.addWidget(self.button_toggle)

        self.listening = False
        self.worker = RecognizerWorker(MainController())
        self.worker.recognized.connect(self.update_transcription)
        self.worker.status_update.connect(self.update_status)

    def toggle_microphone(self):
        self.listening = not self.listening
        if self.listening:
            self.label_status.setText("🎙️ Estou ouvindo...")
            self.button_toggle.setText("Desativar Microfone")
            self.listen_thread = threading.Thread(target=self.worker.listen_loop, daemon=True)
            self.listen_thread.start()
        else:
            self.label_status.setText("🎙️ Aguardando ativação...")
            self.button_toggle.setText("Ativar Microfone")
            self.label_transcription.setText("")
            self.worker.stop_listening()

    def update_transcription(self, texto):
        self.label_transcription.setText(texto)

    def update_status(self, texto):
        self.label_status.setText(texto)


def run_gui():
    app = QApplication(sys.argv)
    window = MarvinGUI()
    window.show()
    sys.exit(app.exec())
