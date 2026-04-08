# backend/main_controller.py
import os
import time
import traceback
import re

from dotenv import load_dotenv

from app.core.config_manager import ConfigManager
from app.services.spotify_service import SpotifyService
from app.services.system_service import SystemService
from app.services.youtube_service import YouTubeService
from app.services.whatsapp_service import WhatsAppService

from app.voice_interface.speech_recognizer import SpeechRecognizer
from app.voice_interface.speech_synthesizer import SpeechSynthesizer

from app.ai.tool_registry import ToolRegistry
from app.ai.ai_processor import AIProcessor
from app.ai.service_registrar import register_all


class MainController:
    def __init__(self):
        print("Initializing MainController...")
        self.config_manager = None
        self.spotify_service = None
        self.system_service = None
        self.youtube_service = None
        self.whatsapp_service = None
        self.speech_recognizer = None
        self.speech_synthesizer = None
        self.tool_registry = None
        self.ai_processor = None

        try:
            backend_root_path = os.path.dirname(os.path.abspath(__file__))
            project_root_env = os.path.join(os.path.dirname(backend_root_path), '.env')
            backend_env = os.path.join(backend_root_path, '.env')

            env_path_to_use = project_root_env if os.path.exists(project_root_env) else (
                backend_env if os.path.exists(backend_env) else None
            )
            if env_path_to_use:
                load_dotenv(dotenv_path=env_path_to_use)
                print(f"MainController: Loading .env from {env_path_to_use}")
            else:
                print("MainController: .env not found, relying on environment variables.")

            self.config_manager = ConfigManager(env_file_path=env_path_to_use)
            print("MainController: ConfigManager initialized.")

            # ── Services (each wrapped so one failure doesn't abort init) ──
            try:
                self.spotify_service = SpotifyService(self.config_manager)
                print("MainController: SpotifyService initialized.")
            except Exception as e:
                print(f"MainController: SpotifyService skipped — {e}")

            try:
                self.system_service = SystemService(self.config_manager)
                print("MainController: SystemService initialized.")
            except Exception as e:
                print(f"MainController: SystemService skipped — {e}")

            try:
                self.youtube_service = YouTubeService(self.config_manager)
                print("MainController: YouTubeService initialized.")
            except Exception as e:
                print(f"MainController: YouTubeService skipped — {e}")

            try:
                self.whatsapp_service = WhatsAppService(self.config_manager)
                print("MainController: WhatsAppService initialized.")
            except Exception as e:
                print(f"MainController: WhatsAppService skipped — {e}")

            # ── AI: ToolRegistry + AIProcessor ──────────────────────────────
            self.tool_registry = ToolRegistry()
            registered = register_all(
                self.tool_registry,
                spotify=self.spotify_service,
                youtube=self.youtube_service,
                whatsapp=self.whatsapp_service,
                system=self.system_service,
            )
            print(f"MainController: {len(registered)} ferramentas registradas: {registered}")

            groq_api_key = self.config_manager.get_groq_api_key()
            if not groq_api_key:
                raise ValueError("GROQ_API_KEY não encontrado no .env")

            self.ai_processor = AIProcessor(
                api_key=groq_api_key,
                tool_registry=self.tool_registry,
            )
            print("MainController: AIProcessor initialized.")

            # ── Voice interface ──────────────────────────────────────────────
            try:
                self.speech_recognizer = SpeechRecognizer()
                print("MainController: SpeechRecognizer initialized.")
                self.speech_recognizer.adjust_for_ambient_noise()
            except Exception as e:
                print(f"MainController: SpeechRecognizer skipped — {e}")

            try:
                self.speech_synthesizer = SpeechSynthesizer()
                print("MainController: SpeechSynthesizer initialized.")
            except Exception as e:
                print(f"MainController: SpeechSynthesizer skipped — {e}")

            print("MainController initialized.")

        except ValueError as ve:
            print(f"FATAL: Configuration error: {ve}")
            raise
        except Exception as e:
            print(f"FATAL: Unexpected error: {e}")
            traceback.print_exc()
            raise

    def process_command_text(self, command_text: str) -> str:
        """Process a text command via AIProcessor (Groq + ToolRegistry)."""
        if not command_text:
            return "Nenhum comando recebido."

        if not self.ai_processor:
            return "Desculpe, o processador de IA não está disponível agora."

        return self.ai_processor.process(command_text)


    def run_voice_loop(self):
        """
        Main loop for voice interaction.
        """
        if not all([self.speech_recognizer, self.speech_synthesizer, self.intent_processor]):
            print("MainController: Core components (STT, TTS, or IntentProcessor) not fully initialized. Voice loop cannot run.")
            if self.speech_synthesizer:
                self.speech_synthesizer.speak("Interface de voz ou processador de comandos não inicializado corretamente. Não posso operar.")
            return
        
        print("\nMarvin (Backend com IntentProcessor) está pronto. Diga 'Marvin' seguido do seu comando.")
        self.speech_synthesizer.speak("Marvin está pronto.")

        active = True
        while active:
            try:
                print("Ouvindo o comando com a palavra de ativação 'Marvin'...")
                full_transcription = self.speech_recognizer.listen_for_audio_input()
                
                command_to_process = None

                if full_transcription:
                    print(f"Transcrição completa: '{full_transcription}'")
                    # Using regex for case-insensitive "marvin" extraction
                    match_marvin = re.search(r'marvin', full_transcription, re.IGNORECASE)
                    if match_marvin:
                        # Extract command after "Marvin" (preserving original case of the command part)
                        command_start_index = match_marvin.end()
                        command_to_process = full_transcription[command_start_index:].strip()
                        
                        if command_to_process:
                            print(f"Comando para Marvin: '{command_to_process}'")
                        else:
                            # "Marvin" was said, but no clear command followed
                            self.speech_synthesizer.speak("Sim?") 
                            continue 
                    # else: # No wake word, ignore in this mode
                    #     pass 
                
                if command_to_process:
                    response = self.process_command_text(command_to_process)
                    print(f"Resposta do Marvin: {response}")
                    self.speech_synthesizer.speak(response)

                    if any(kw in response.lower() for kw in ["até logo", "tchau", "desligando"]):
                        active = False 
                
            except KeyboardInterrupt:
                print("\nSaindo do Marvin via KeyboardInterrupt.")
                if self.speech_synthesizer: self.speech_synthesizer.speak("Desligando.")
                active = False
            except Exception as e:
                print(f"Um erro ocorreu no loop de voz: {e}")
                traceback.print_exc()
                if self.speech_synthesizer: self.speech_synthesizer.speak("Ocorreu um erro interno. Por favor, tente novamente.")
                time.sleep(1) 
        
        print("Marvin encerrado.")
        if self.youtube_service:
            self.youtube_service.quit_driver()


if __name__ == '__main__':
    try:
        controller = MainController()
        
        if controller.config_manager and controller.intent_processor and \
           controller.speech_recognizer and controller.speech_synthesizer:
            
            print("\n--- Testando o processamento de texto do MainController via IntentProcessor ---")
            
            # Test cases for IntentProcessor (ensure your regexes in IntentProcessor are comprehensive)
            test_commands = [
                "Que horas são?",
                "Tocar música Bohemian Rhapsody",
                "Pause a música",
                "Abrir aplicativo Notepad", # ou Bloco de Notas se sua regex for em PT
                "Pesquisar vídeos de gatos engraçados no YouTube", # Exemplo, adapte ao seu IntentProcessor
                "Enviar mensagem para Contato Teste dizendo olá tudo bem", # Exemplo
                "Tchau"
            ]

            for cmd in test_commands:
                print(f"\nComando de Teste: '{cmd}'")
                response = controller.process_command_text(cmd)
                print(f"Resposta: {response}")
                if "desligando" in response.lower() or "até logo" in response.lower():
                    print("Comando de desligamento recebido no teste de texto.")
                    # break # Uncomment if you want to stop tests on shutdown command

            print("\n--- Iniciando Loop de Voz do MainController (Ctrl+C para sair) ---")
            controller.run_voice_loop()
        else:
            print("MainController não pôde inicializar componentes essenciais. Loop de voz e testes de texto não iniciados.")

    except Exception as e:
        print(f"Erro na execução do exemplo do MainController: {e}")
        traceback.print_exc()