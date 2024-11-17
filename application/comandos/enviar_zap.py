import webbrowser
import time
import pyautogui
import pyperclip


def enviar_mensagem_whatsapp(contato, mensagem):
    # Abre o WhatsApp Web no navegador padrão
    webbrowser.open("https://web.whatsapp.com")

    # Aguarda tempo suficiente para o WhatsApp Web carregar
    time.sleep(10)  # Ajuste conforme necessário para o tempo de carregamento

    # Simula a abertura da barra de pesquisa do WhatsApp (Ctrl + Alt + /)
    pyautogui.hotkey("ctrl", "alt", "/")

    # Apaga qualquer texto residual na barra de pesquisa
    pyautogui.hotkey("ctrl", "a")
    pyautogui.press("backspace")

    # Digita o nome do contato
    text = contato
    pyperclip.copy(text)
    pyautogui.hotkey('ctrl', 'v')

    pyautogui.press("enter")
    # Espera o chat abrir

    # Digita a mensagem
    text = mensagem
    pyperclip.copy(text)
    pyautogui.hotkey('ctrl', 'v')

    pyautogui.press("enter")

    print(f"Mensagem enviada para {contato}!")
