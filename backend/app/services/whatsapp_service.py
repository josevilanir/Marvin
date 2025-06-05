# backend/app/services/whatsapp_service.py
import webbrowser
import time
import os

# Ajuste: Tentar definir DISPLAY somente se não estiver rodando headless
if "DISPLAY" not in os.environ and not os.environ.get("PYTHON_HEADLESS"):
    os.environ["DISPLAY"] = ":0"

try:
    import pyautogui  # For UI automation
    import pyperclip  # For reliable copy-pasting, especially with special characters
    pyautogui_available = True
except Exception as e:
    print(f"WhatsAppService: PyAutoGUI not available due to: {e}")
    pyautogui_available = False

from app.core.config_manager import ConfigManager

class WhatsAppService:
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.whatsapp_web_load_time = 15
        self.action_delay = 1.5

    def send_message(self, contact_name: str, message: str) -> dict:
        if not pyautogui_available:
            return {"status": "error", "message": "PyAutoGUI or dependencies not available in this environment."}

        if not contact_name or not message:
            return {"status": "error", "message": "Contact name and message are required."}

        try:
            print(f"WhatsAppService: Opening WhatsApp Web...")
            webbrowser.open("https://web.whatsapp.com")
            print(f"WhatsAppService: Waiting {self.whatsapp_web_load_time}s for WhatsApp Web to load.")
            time.sleep(self.whatsapp_web_load_time)

            print("WhatsAppService: Please ensure the WhatsApp Web browser window is active and focused.")
            time.sleep(3)

            print("WhatsAppService: Activating contact search...")
            pyautogui.hotkey("ctrl", "alt", "/")
            time.sleep(self.action_delay)

            pyautogui.hotkey("ctrl", "a")
            time.sleep(0.2)
            pyautogui.press("backspace")
            time.sleep(self.action_delay)

            print(f"WhatsAppService: Typing contact name: {contact_name}")
            pyperclip.copy(contact_name)
            pyautogui.hotkey('ctrl', 'v')
            time.sleep(self.action_delay)

            print("WhatsAppService: Selecting contact...")
            pyautogui.press("enter")
            time.sleep(self.action_delay * 2)

            print(f"WhatsAppService: Typing message: {message}")
            pyperclip.copy(message)
            pyautogui.hotkey('ctrl', 'v')
            time.sleep(self.action_delay)

            print("WhatsAppService: Sending message...")
            pyautogui.press("enter")
            time.sleep(self.action_delay)

            return {"status": "success", "message": f"Message sent to '{contact_name}' (or attempt initiated)."}

        except FileNotFoundError:
            return {"status": "error", "message": "Clipboard error. On Linux, install 'xclip' or 'xsel'."}
        except Exception as e:
            print(f"WhatsAppService: Error during WhatsApp automation: {e}")
            return {"status": "error", "message": f"Error during WhatsApp automation: {e}"}


if __name__ == '__main__':
    class DummyConfigManager:
        pass

    cfg = DummyConfigManager()
    whatsapp_service = WhatsAppService(cfg)

    test_contact = "o negro"  # <<< Altere para um contato real
    test_message = "Olá! Esta é uma mensagem de teste do Marvin. 🤖"

    print(f"\n--- Testing WhatsApp Service ---")
    print(f"Attempting to send: '{test_message}' to '{test_contact}'")
    print("IMPORTANT: Ensure WhatsApp Web is logged in and the browser window becomes active after it opens.")

    result = whatsapp_service.send_message(test_contact, test_message)
    print(f"WhatsApp Send Result: {result}")

    if result["status"] == "error":
        print("\nTroubleshooting tips for WhatsAppService:")
        print("- Verifique se o WhatsApp Web está logado.")
        print("- Certifique-se de que a janela do navegador esteja ativa após abrir.")
        print("- No Linux, verifique se o 'xclip' ou 'xsel' está instalado.")
