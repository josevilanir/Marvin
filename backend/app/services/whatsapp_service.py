# backend/app/services/whatsapp_service.py
import webbrowser
import time
import pyautogui # For UI automation
import pyperclip # For reliable copy-pasting, especially with special characters

# Assuming ConfigManager might be used for future settings (e.g., default wait times)
from app.core.config_manager import ConfigManager

class WhatsAppService:
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        # Consider making these configurable via config_manager
        self.whatsapp_web_load_time = 15 # Increased from original 10s
        self.action_delay = 1.5 # Delay between pyautogui actions

    def send_message(self, contact_name: str, message: str) -> dict:
        """
        Sends a WhatsApp message to a specified contact.
        Relies on PyAutoGUI for UI automation of WhatsApp Web.
        Based on enviar_mensagem_whatsapp from
        """
        if not contact_name or not message:
            return {"status": "error", "message": "Contact name and message are required."}

        try:
            print(f"WhatsAppService: Opening WhatsApp Web...")
            webbrowser.open("https://web.whatsapp.com")
            print(f"WhatsAppService: Waiting {self.whatsapp_web_load_time}s for WhatsApp Web to load and for QR scan if needed.")
            time.sleep(self.whatsapp_web_load_time) # Wait for page to load & QR scan

            # Ensure WhatsApp Web window is active. This is crucial for PyAutoGUI.
            # User might need to manually focus the window.
            # Consider adding a brief pause here for the user to ensure the window is active.
            print("WhatsAppService: Please ensure the WhatsApp Web browser window is active and focused.")
            time.sleep(3) 

            # Step 1: Focus search bar for contacts
            # Original: Ctrl + Alt + / - This is a shortcut for global search
            # A more common way to search contacts once chats are loaded is to click the chat search input.
            # Let's stick to the original shortcut for now, assuming it's intended for finding contacts.
            # If it doesn't work, an alternative would be to click a known coordinate for the search bar,
            # or use image recognition if PyAutoGUI's capabilities are extended.
            
            print("WhatsAppService: Activating contact search...")
            pyautogui.hotkey("ctrl", "alt", "/") # Global contact search
            time.sleep(self.action_delay)

            # Clear any existing text (original used Ctrl+A, Backspace)
            pyautogui.hotkey("ctrl", "a")
            time.sleep(0.2)
            pyautogui.press("backspace")
            time.sleep(self.action_delay)
            
            # Type contact name using pyperclip for reliability
            print(f"WhatsAppService: Typing contact name: {contact_name}")
            pyperclip.copy(contact_name)
            pyautogui.hotkey('ctrl', 'v')
            time.sleep(self.action_delay)

            # Press Enter to select the contact from search results
            print("WhatsAppService: Selecting contact...")
            pyautogui.press("enter")
            time.sleep(self.action_delay * 2) # Allow chat to load

            # Type message using pyperclip
            print(f"WhatsAppService: Typing message: {message}")
            pyperclip.copy(message)
            pyautogui.hotkey('ctrl', 'v')
            time.sleep(self.action_delay)

            # Press Enter to send the message
            print("WhatsAppService: Sending message...")
            pyautogui.press("enter")
            time.sleep(self.action_delay) # Small delay after sending

            return {"status": "success", "message": f"Message sent to '{contact_name}' (or attempt initiated)."}

        except FileNotFoundError: # pyperclip might raise this if xclip/xsel not on Linux
            return {"status": "error", "message": "Error with clipboard utility (pyperclip). Ensure xclip or xsel is installed on Linux."}
        except Exception as e:
            # PyAutoGUI can fail for various reasons (permissions, display server issues on Linux, window not focused)
            print(f"WhatsAppService: Error during WhatsApp automation: {e}")
            return {"status": "error", "message": f"Error during WhatsApp automation: {e}. Ensure WhatsApp Web window was active and focused."}


if __name__ == '__main__':
    # Example Usage
    # Create a dummy ConfigManager for testing
    class DummyConfigManager:
        pass
    
    cfg = DummyConfigManager()
    whatsapp_service = WhatsAppService(cfg)

    # IMPORTANT: This test will attempt to control your mouse and keyboard
    # to interact with WhatsApp Web.
    # 1. Make sure you are logged into WhatsApp Web in your default browser.
    # 2. Run this script.
    # 3. Quickly switch to and focus the WhatsApp Web browser window after it opens.
    #    You have about whatsapp_web_load_time + 3 seconds.
    
    test_contact = "o negro"  # <<< CHANGE THIS TO A REAL CONTACT/GROUP FOR TESTING
    test_message = "Olá! Esta é uma mensagem de teste do Marvin. 🤖"

    if test_contact == "NomeDoSeuContatoOuGrupoParaTeste":
        print("Please change 'test_contact' variable to a real contact name for testing.")
    else:
        print(f"\n--- Testing WhatsApp Service ---")
        print(f"Attempting to send: '{test_message}' to '{test_contact}'")
        print("IMPORTANT: Ensure WhatsApp Web is logged in and the browser window becomes active after opening.")
        
        result = whatsapp_service.send_message(test_contact, test_message)
        print(f"WhatsApp Send Result: {result}")

        if result["status"] == "error":
            print("\nTroubleshooting tips for WhatsAppService:")
            print("- Was WhatsApp Web already logged in (QR code scanned)?")
            print("- Did you quickly make the WhatsApp Web browser window active and focused after it opened?")
            print("- Are keyboard layouts consistent? (PyAutoGUI types based on US layout by default for special chars if not careful)")
            print("- On Linux, ensure `scrot` (for screenshots, sometimes a dependency) and `xclip` or `xsel` (for pyperclip) are installed.")
            print("- Check for any pop-ups or unexpected UI elements in WhatsApp Web.")