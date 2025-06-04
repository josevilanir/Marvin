import sys
from unittest.mock import MagicMock
from unittest.mock import patch, call


# Mock para evitar dependência gráfica no ambiente
sys.modules['mouseinfo'] = MagicMock()
sys.modules['pyautogui'] = MagicMock()

import pytest
from unittest.mock import patch
from backend.app.services.whatsapp_service import WhatsAppService

@pytest.fixture
def service():
    mock_config = MagicMock()
    return WhatsAppService(mock_config)

def test_send_message_missing_fields(service):
    result = service.send_message("", "")
    assert result["status"] == "error"
    assert "Contact name and message are required" in result["message"]

def test_send_message_success(service):
    with patch("backend.app.services.whatsapp_service.webbrowser.open") as mock_open, \
         patch("backend.app.services.whatsapp_service.pyautogui.hotkey"), \
         patch("backend.app.services.whatsapp_service.time.sleep"), \
         patch("backend.app.services.whatsapp_service.pyautogui.typewrite"), \
         patch("backend.app.services.whatsapp_service.pyperclip.copy"):
        result = service.send_message("João", "Olá!")
        assert result["status"] == "success"
        assert "Message sent to 'João'" in result["message"]

def test_send_message_missing_contact(service):
    result = service.send_message("", "Oi")
    assert result["status"] == "error"
    assert "Contact name and message are required" in result["message"]

@patch("backend.app.services.whatsapp_service.pyperclip.copy", side_effect=Exception("Clipboard error"))
def test_send_message_clipboard_error(mock_copy, service):
    result = service.send_message("João", "Olá!")
    assert result["status"] == "error"
    assert "Clipboard error" in result["message"]

@patch("backend.app.services.whatsapp_service.pyperclip.copy")
@patch("backend.app.services.whatsapp_service.pyautogui.press", side_effect=Exception("Generic error"))
def test_send_message_generic_exception(mock_press, mock_copy, service):
    result = service.send_message("João", "Tudo bem?")
    assert result["status"] == "error"
    assert "Generic error" in result["message"]

@patch("backend.app.services.whatsapp_service.webbrowser.open")
def test_url_format_correct(mock_open, service):
    service.send_message("Maria", "Bom dia!")
    mock_open.assert_called_once()
    url = mock_open.call_args[0][0]
    assert "https://web.whatsapp.com" in url

def test_message_with_accents(service):
    with patch("backend.app.services.whatsapp_service.pyperclip.copy") as mock_copy:
        service.send_message("Carlos", "Olá, você está bem?")
        mock_copy.assert_has_calls([
            call("Carlos"),
            call("Olá, você está bem?")
        ])

def test_execution_time_simulation(service):
    with patch("backend.app.services.whatsapp_service.time.sleep") as mock_sleep:
        service.send_message("Paula", "Bom dia!")
        assert mock_sleep.call_count >= 3  # espera mínima: abrir site, digitar contato, digitar msg
