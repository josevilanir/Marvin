# backend/app/services/system_service.py
import subprocess
import platform
import os
import shutil
import webbrowser
from datetime import datetime
import threading
import time
import pygame # For timer alarm

# Assuming ConfigManager might be needed for paths or future settings
from app.core.config_manager import ConfigManager 
# Assuming constants might define resource paths
from app.core.constants import RESOURCE_PATH # You'll need to define this in constants.py

try:
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
    from ctypes import cast, POINTER
    from comtypes import CLSCTX_ALL
    PYCAW_AVAILABLE = True
except ImportError:
    PYCAW_AVAILABLE = False
    print("SystemService: pycaw library not found. Volume control will not be available.")


class SystemService:
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        # Define path for alarm sound. This should come from a reliable source.
        # For now, assuming it's in a 'resources' folder relative to the app's root.
        # RESOURCE_PATH should be defined in app/core/constants.py, e.g.
        # RESOURCE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'resources')
        # For `despertador.mp3`, if it's now in backend/app/resources/
        # We need to ensure RESOURCE_PATH in constants.py correctly points there.
        # For now, let's assume a path structure that can be made configurable.
        # The original path in timer.py was "C:/Users/Vilanir/Marvin/utils/despertador.mp3"
        # We should make this path relative and configurable.
        
        # Let's define a placeholder for the alarm sound path
        # It should ideally be set via constants.py or config_manager
        self.alarm_sound_path = None
        if RESOURCE_PATH: # Check if RESOURCE_PATH is defined
            self.alarm_sound_path = os.path.join(RESOURCE_PATH, "despertador.mp3")
            if not os.path.exists(self.alarm_sound_path):
                 print(f"SystemService Warning: Alarm sound not found at {self.alarm_sound_path}. Timer alarm will be silent.")
                 self.alarm_sound_path = None # Disable if not found
        else:
            print("SystemService Warning: RESOURCE_PATH not defined. Alarm sound path cannot be determined.")

        # Initialize pygame mixer for the alarm if not already done by SpeechSynthesizer
        # However, SpeechSynthesizer quits mixer in __del__. This could conflict.
        # It's better if the alarm sound playback is self-contained or shares the mixer carefully.
        # For simplicity, timer will initialize and quit its own mixer instance for the alarm.
        # This avoids conflicts if SpeechSynthesizer is also active.

    def get_current_datetime_string(self) -> dict:
        """
        Gets the current time and formats it as a spoken response.
        Based on comandos/data_e_hora.py
        """
        now = datetime.now()
        # Original format: "São %H:%M."
        time_string = now.strftime("São %H horas e %M minutos.")
        date_string = now.strftime("Hoje é dia %d de %B de %Y.")
        return {"status": "success", "message": f"{time_string} {date_string}", "time": time_string, "date": date_string}

    def get_marvin_info(self) -> dict:
        """
        Provides a short description of Marvin.
        Based on comandos/sobre_mim.py
        """
        info = "Eu sou Marvin, seu assistente pessoal. Estou aqui para ajudar no que precisar!"
        # Original: "Eu sou Marvin, a assistente pessoal criada por José Vilanir, mais conhecido como o rei das mitadas"
        # You can customize this message.
        return {"status": "success", "message": info}

    def open_application(self, app_name: str) -> dict:
        """
        Opens a specified application on Windows.
        Search order: known aliases → PATH (shutil.which) → common install paths → desktop shortcut.
        """
        app_name_lower = app_name.lower().strip()
        current_os = platform.system().lower()

        # Map of aliases → executable names (or full paths as fallbacks)
        ALIASES: dict[str, list[str]] = {
            "bloco de notas": ["notepad.exe"],
            "notepad":        ["notepad.exe"],
            "calculadora":    ["calc.exe"],
            "calculator":     ["calc.exe"],
            "chrome":         ["chrome.exe"],
            "google chrome":  ["chrome.exe"],
            "firefox":        ["firefox.exe"],
            "edge":           ["msedge.exe"],
            "steam":          ["steam.exe"],
            "spotify":        ["Spotify.exe"],
            "discord":        ["Discord.exe", "discord.exe"],
            "vscode":         ["code.exe", "Code.exe"],
            "visual studio code": ["code.exe"],
            "code":           ["code.exe"],
            "explorer":       ["explorer.exe"],
            "task manager":   ["Taskmgr.exe"],
            "gerenciador de tarefas": ["Taskmgr.exe"],
            "brave":          ["brave.exe"],
            "brave browser":  ["brave.exe"],
        }

        # Known full paths for apps installed in deep subdirectories
        KNOWN_PATHS: dict[str, list[str]] = {
            "brave.exe": [
                os.path.expandvars(r"%LOCALAPPDATA%\BraveSoftware\Brave-Browser\Application\brave.exe"),
                os.path.expandvars(r"%PROGRAMFILES%\BraveSoftware\Brave-Browser\Application\brave.exe"),
            ],
            "chrome.exe": [
                os.path.expandvars(r"%PROGRAMFILES%\Google\Chrome\Application\chrome.exe"),
                os.path.expandvars(r"%PROGRAMFILES(X86)%\Google\Chrome\Application\chrome.exe"),
                os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
            ],
            "steam.exe": [
                os.path.expandvars(r"%PROGRAMFILES(X86)%\Steam\steam.exe"),
                os.path.expandvars(r"%PROGRAMFILES%\Steam\steam.exe"),
            ],
            "Spotify.exe": [
                os.path.expandvars(r"%APPDATA%\Spotify\Spotify.exe"),
            ],
            "Discord.exe": [
                os.path.expandvars(r"%LOCALAPPDATA%\Discord\Update.exe"),
                os.path.expandvars(r"%LOCALAPPDATA%\Discord\app-\Discord.exe"),
            ],
        }

        # Common Windows search paths in addition to PATH
        SEARCH_DIRS = [
            os.path.expandvars(r"%PROGRAMFILES%"),
            os.path.expandvars(r"%PROGRAMFILES(X86)%"),
            os.path.expandvars(r"%LOCALAPPDATA%"),
            os.path.expandvars(r"%APPDATA%"),
        ]

        def find_exe(exe_name: str) -> str | None:
            """Return full path to exe_name if found, else None."""
            # 1. Check PATH
            found = shutil.which(exe_name)
            if found:
                return found
            # 2. Check known deep paths
            for known_exe, paths in KNOWN_PATHS.items():
                if known_exe.lower() == exe_name.lower():
                    for p in paths:
                        if os.path.isfile(p):
                            return p
            # 3. Walk common install dirs (one level deep)
            for base in SEARCH_DIRS:
                if not os.path.isdir(base):
                    continue
                try:
                    for entry in os.scandir(base):
                        if entry.is_dir(follow_symlinks=False):
                            candidate = os.path.join(entry.path, exe_name)
                            if os.path.isfile(candidate):
                                return candidate
                        elif entry.name.lower() == exe_name.lower():
                            return entry.path
                except PermissionError:
                    continue
            return None

        def launch(path: str) -> bool:
            """Launch path via os.startfile (Windows). Returns True on success."""
            try:
                os.startfile(path)
                return True
            except Exception:
                return False

        # --- Resolve candidates ---
        exe_candidates: list[str] = ALIASES.get(app_name_lower, [])

        # If not in aliases, treat the raw name as a candidate
        if not exe_candidates:
            raw = app_name_lower if app_name_lower.endswith(".exe") else app_name_lower + ".exe"
            exe_candidates = [raw]

        # --- Try to find and launch ---
        if current_os == "windows":
            for exe in exe_candidates:
                full_path = find_exe(exe)
                if full_path and launch(full_path):
                    return {"status": "success", "message": f"Abrindo '{app_name}'."}

            # Fallback: desktop shortcut
            desktop = os.path.join(os.path.expanduser("~"), "Desktop")
            for name_variant in [app_name, app_name_lower]:
                shortcut = os.path.join(desktop, f"{name_variant}.lnk")
                if os.path.exists(shortcut) and launch(shortcut):
                    return {"status": "success", "message": f"Abrindo atalho '{app_name}' da área de trabalho."}

            return {"status": "error", "message": f"Não consegui encontrar ou abrir '{app_name}'. Verifique se está instalado."}

        # --- Non-Windows fallback ---
        cmd = shutil.which(app_name_lower)
        if cmd:
            try:
                subprocess.Popen([cmd])
                return {"status": "success", "message": f"Abrindo '{app_name}'."}
            except Exception as e:
                return {"status": "error", "message": f"Erro ao abrir '{app_name}': {e}"}

        return {"status": "error", "message": f"Não sei como abrir '{app_name}' no sistema {current_os}."}

    def open_calculator(self) -> dict:
        """Opens the system calculator."""
        # This can now call open_application for better consistency
        return self.open_application("calculadora")

    def search_web(self, query: str) -> dict:
        """
        Opens the default web browser and performs a Google search.
        Based on comandos/abrir_navegador.py
        """
        if not query:
            return {"status": "error", "message": "Nenhum termo de pesquisa fornecido."}
        try:
            url = f"https://www.google.com/search?q={query}"
            webbrowser.open(url)
            return {"status": "success", "message": f"Pesquisando por '{query}' na web."}
        except Exception as e:
            return {"status": "error", "message": f"Erro ao abrir navegador: {e}"}

    def _interpret_timer_duration(self, duration_str: str) -> float | None:
        """
        Interprets a string like "5 minutos", "1 hora", "30 segundos" into seconds.
        Based on comandos/timer.py
        """
        try:
            duration_str = duration_str.lower().strip()
            parts = duration_str.split()
            if not parts:
                return None
            
            value = float(parts[0]) # Expects number first

            if "hora" in duration_str or "horas" in duration_str:
                return value * 3600
            elif "minuto" in duration_str or "minutos" in duration_str:
                return value * 60
            elif "segundo" in duration_str or "segundos" in duration_str:
                return value
            else: # Assume seconds if no unit, or if only a number is given
                return value
        except ValueError:
            print(f"Timer: Error: '{duration_str}' não é um valor de tempo válido.")
            return None
        except IndexError:
             print(f"Timer: Error: formato de duração inválido '{duration_str}'.")
             return None


    def _timer_thread_target(self, duration_seconds: float, original_duration_str: str):
        """Target function for the timer thread."""
        print(f"Timer: Iniciado para {original_duration_str} ({duration_seconds}s).")
        time.sleep(duration_seconds)
        print(f"Timer: O tempo de {original_duration_str} acabou!")
        
        # Play alarm sound
        if self.alarm_sound_path and os.path.exists(self.alarm_sound_path):
            try:
                pygame.mixer.init() # Independent mixer instance for alarm
                pygame.mixer.music.load(self.alarm_sound_path)
                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy():
                    pygame.time.Clock().tick(10)
                pygame.mixer.quit()
                print("Timer: Alarme sonoro reproduzido.")
            except Exception as e_alarm:
                print(f"Timer: Erro ao tocar alarme: {e_alarm}")
        else:
            print("Timer: Alarme sonoro não configurado ou arquivo não encontrado.")
        
        # Here you could also trigger a callback or event for the MainController/Frontend
        # For now, it just prints. The frontend might need to be notified.

    def start_timer(self, duration_str: str) -> dict:
        """
        Starts a timer in a separate thread.
        Based on comandos/timer.py (iniciar_timer_em_thread)
        """
        duration_seconds = self._interpret_timer_duration(duration_str)
        if duration_seconds is None or duration_seconds <= 0:
            return {"status": "error", "message": f"Duração do timer inválida: '{duration_str}'"}

        try:
            thread = threading.Thread(target=self._timer_thread_target, args=(duration_seconds, duration_str))
            thread.daemon = True # Allows main program to exit even if thread is running
            thread.start()
            return {"status": "success", "message": f"Timer definido para {duration_str}."}
        except Exception as e:
            return {"status": "error", "message": f"Erro ao iniciar timer: {e}"}

    def adjust_system_volume(self, volume_level_str: str) -> dict:
        """
        Adjusts the system master volume.
        Based on comandos/controlar_volume.py
        Volume level should be a string representing a percentage (e.g., "50", "75%").
        """
        if not PYCAW_AVAILABLE:
            return {"status": "error", "message": "Controle de volume não disponível (pycaw não instalado)."}

        try:
            # Clean up input string (e.g., remove '%')
            volume_input = volume_level_str.replace('%', '').strip()
            volume_value_percent = float(volume_input)

            if not (0 <= volume_value_percent <= 100):
                return {"status": "error", "message": "Nível de volume inválido. Use um valor entre 0 e 100."}

            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume_control = cast(interface, POINTER(IAudioEndpointVolume))

            # Set volume (scalar from 0.0 to 1.0)
            volume_control.SetMasterVolumeLevelScalar(volume_value_percent / 100.0, None)
            
            return {"status": "success", "message": f"Volume ajustado para {int(volume_value_percent)}%."}
        except ValueError:
            return {"status": "error", "message": f"Valor de volume inválido: '{volume_level_str}'. Use um número."}
        except Exception as e:
            # This can include com_error if no audio device, etc.
            print(f"SystemService: Erro ao ajustar volume: {e}")
            return {"status": "error", "message": f"Erro ao ajustar volume: {e}"}


if __name__ == '__main__':
    # Create a dummy ConfigManager and Constants for testing
    class DummyConfigManager:
        pass # Add any methods/properties SystemService might expect

    # Define RESOURCE_PATH for testing the timer alarm sound
    # This assumes a structure like marvin_professional/backend/app/services/system_service.py
    # and marvin_professional/backend/app/resources/despertador.mp3
    # You need to create this dummy mp3 or point to an existing one for the test.
    try:
        # Simulate constants.py
        APP_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # app/
        RESOURCE_PATH = os.path.join(APP_ROOT, 'resources')
        if not os.path.exists(RESOURCE_PATH):
            os.makedirs(RESOURCE_PATH)
        
        # Create a dummy despertador.mp3 if it doesn't exist for testing
        dummy_alarm_path = os.path.join(RESOURCE_PATH, "despertador.mp3")
        if not os.path.exists(dummy_alarm_path):
            try:
                from gtts import gTTS
                tts = gTTS("Alarme", lang='pt')
                tts.save(dummy_alarm_path)
                print(f"Dummy alarm sound created at {dummy_alarm_path}")
            except Exception as e_gtts:
                print(f"Could not create dummy alarm sound using gTTS: {e_gtts}")
                print("Timer alarm sound test may fail or be silent.")


        cfg_manager = DummyConfigManager()
        system_service = SystemService(cfg_manager)

        print("\n--- Testando SystemService ---")

        print(f"Data e Hora: {system_service.get_current_datetime_string()}")
        print(f"Info Marvin: {system_service.get_marvin_info()}")
        
        # Test opening apps (these might only work on specific OS or if apps are in PATH)
        # print(f"Abrir Calculadora: {system_service.open_calculator()}")
        # time.sleep(2) # Give time for app to open
        # print(f"Abrir Bloco de Notas: {system_service.open_application('bloco de notas')}")
        # time.sleep(2)

        print(f"Pesquisar 'python na web': {system_service.search_web('python')}")

        if PYCAW_AVAILABLE:
            print(f"Ajustar Volume para 30%: {system_service.adjust_system_volume('30')}")
            current_volume = AudioUtilities.GetSpeakers().Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            current_scalar = cast(current_volume, POINTER(IAudioEndpointVolume)).GetMasterVolumeLevelScalar()
            print(f"Volume atual do sistema: {current_scalar*100:.0f}% (verifique manualmente)")
        else:
            print("Teste de volume pulado (pycaw não disponível).")

        print("\nTestando Timer (5 segundos)...")
        print(system_service.start_timer("5 segundos"))
        print("Timer iniciado em background. Aguarde o alarme...")
        time.sleep(7) # Wait for timer to finish and play sound

        print("\nTestando Timer (formato '1 minuto')...")
        print(system_service.start_timer("0.1 minutos")) # 6 segundos
        time.sleep(8)


        print("\n--- Testes SystemService Concluídos ---")

    except Exception as e:
        print(f"Erro no exemplo do SystemService: {e}")
        import traceback
        traceback.print_exc()