# backend/main_controller.py
import os
import time # For timer example
import traceback
import re # For case-insensitive split in the voice loop

# Assuming your services and core modules are in the 'app' package
from app.core.config_manager import ConfigManager
from app.services.spotify_service import SpotifyService
from app.services.system_service import SystemService
from app.services.youtube_service import YouTubeService
from app.services.whatsapp_service import WhatsAppService

from app.voice_interface.speech_recognizer import SpeechRecognizer
from app.voice_interface.speech_synthesizer import SpeechSynthesizer

# Import the new IntentProcessor
from app.nlp.intent_processor import IntentProcessor


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
        self.intent_processor = None # Initialize IntentProcessor instance

        try:
            backend_root_path = os.path.dirname(os.path.abspath(__file__)) # backend/
            project_root_env = os.path.join(os.path.dirname(backend_root_path), '.env')
            backend_env = os.path.join(backend_root_path, '.env')

            env_path_to_use = None
            if os.path.exists(project_root_env):
                env_path_to_use = project_root_env
            elif os.path.exists(backend_env):
                env_path_to_use = backend_env
            
            if env_path_to_use:
                print(f"MainController: Loading .env from {env_path_to_use}")
            else:
                print("MainController: .env file not found in standard locations. Relying on environment variables.")

            self.config_manager = ConfigManager(env_file_path=env_path_to_use)
            print("MainController: ConfigManager initialized.")

            # Initialize services
            try:
                self.spotify_service = SpotifyService(self.config_manager)
                print("MainController: SpotifyService initialized.")
            except Exception as e_spotify:
                print(f"MainController: Error initializing SpotifyService: {e_spotify}")
                traceback.print_exc()
            
            try:
                self.system_service = SystemService(self.config_manager)
                print("MainController: SystemService initialized.")
            except Exception as e_system:
                print(f"MainController: Error initializing SystemService: {e_system}")
                traceback.print_exc()

            try:
                self.youtube_service = YouTubeService(self.config_manager)
                print("MainController: YouTubeService initialized.")
            except Exception as e_youtube:
                print(f"MainController: Error initializing YouTubeService: {e_youtube}")
                traceback.print_exc()

            try:
                self.whatsapp_service = WhatsAppService(self.config_manager)
                print("MainController: WhatsAppService initialized.")
            except Exception as e_whatsapp:
                print(f"MainController: Error initializing WhatsAppService: {e_whatsapp}")
                traceback.print_exc()

            # Initialize IntentProcessor, passing self (MainController instance)
            # so IntentProcessor can access the services.
            self.intent_processor = IntentProcessor(self)
            print("MainController: IntentProcessor initialized.")

            # Initialize voice interface
            try:
                self.speech_recognizer = SpeechRecognizer()
                print("MainController: SpeechRecognizer initialized.")
                self.speech_recognizer.adjust_for_ambient_noise()
            except Exception as e_sr:
                print(f"MainController: Error initializing SpeechRecognizer: {e_sr}")
                traceback.print_exc()

            try:
                self.speech_synthesizer = SpeechSynthesizer()
                print("MainController: SpeechSynthesizer initialized.")
            except Exception as e_ss:
                print(f"MainController: Error initializing SpeechSynthesizer: {e_ss}")
                traceback.print_exc()
            
            print("MainController initialized (potentially with some service errors).")

        except ValueError as ve: 
            print(f"FATAL: Configuration error during MainController initialization: {ve}")
            raise
        except Exception as e:
            print(f"FATAL: Unexpected error during MainController initialization: {e}")
            traceback.print_exc()
            raise

    def process_command_text(self, command_text: str) -> str:
        """
        Processes a text command by delegating to the IntentProcessor.
        """
        if not command_text:
            return "Nenhum comando recebido."
        
        if not self.intent_processor:
            print("MainController: IntentProcessor not initialized. Cannot process command.")
            return "Desculpe, estou com problemas para processar comandos agora."

        # Delegate the entire command processing to IntentProcessor
        response_message = self.intent_processor.process(command_text)
        
        return response_message


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