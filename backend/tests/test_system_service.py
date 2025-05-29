# backend/tests/test_system_service.py
import pytest
from unittest.mock import patch, MagicMock # Para mocks
from datetime import datetime

# Importe a classe que você quer testar
from app.services import SystemService
from backend.app.core.config_manager import ConfigManager # Ou um DummyConfigManager para testes

# Se ConfigManager for complexo de instanciar, podemos mocká-lo ou criar um dummy
class DummyConfigManager:
    pass # Não precisa de funcionalidade real para todos os testes do SystemService

# Fixture do pytest para criar uma instância do SystemService para cada teste
@pytest.fixture
def system_service():
    """Retorna uma instância de SystemService com um ConfigManager mockado/dummy."""
    dummy_config = DummyConfigManager()
    service = SystemService(config_manager=dummy_config)
    return service

# --- Testes para get_current_datetime_string ---
def test_get_current_datetime_string_returns_dict_with_status_success(system_service):
    result = system_service.get_current_datetime_string()
    assert isinstance(result, dict)
    assert result.get("status") == "success"

@patch('backend.app.services.system_service.datetime') # Mockar o módulo datetime DENTRO do system_service
def test_get_current_datetime_string_formats_message_correctly(mock_datetime, system_service):
    # Arrange: Configure o mock para retornar uma data/hora específica
    fixed_now = datetime(2024, 5, 28, 10, 30, 0) # 28 de Maio de 2024, 10:30:00
    mock_datetime.now.return_value = fixed_now
    
    # Act
    result = system_service.get_current_datetime_string()
    
    # Assert
    expected_time_string = "São 10 horas e 30 minutos."
    expected_date_string = "Hoje é dia 28 de maio de 2024." # Ajuste o "maio" se seu locale for diferente
    
    assert result.get("message") == f"{expected_time_string} {expected_date_string}"
    assert result.get("time") == expected_time_string
    assert result.get("date") == expected_date_string
    mock_datetime.now.assert_called_once() # Verifica se datetime.now() foi chamado

# --- Testes para get_marvin_info ---
def test_get_marvin_info_returns_expected_message(system_service):
    result = system_service.get_marvin_info()
    assert result.get("status") == "success"
    assert "Eu sou Marvin" in result.get("message") # Verifica parte da mensagem

# --- Testes para open_calculator (exemplo com mock de subprocess) ---
@patch('backend.app.services.system_service.platform')
@patch('backend.app.services.system_service.subprocess.Popen')
def test_open_calculator_windows(mock_popen, mock_platform, system_service):
    # Arrange
    mock_platform.system.return_value = "Windows" # Simula estar no Windows
    
    # Act
    result = system_service.open_calculator()
    
    # Assert
    assert result.get("status") == "success"
    assert "Abrindo 'calculadora'" in result.get("message")
    mock_popen.assert_called_once_with(["calc.exe"], shell=True)
    mock_platform.system.assert_called_once()

@patch('backend.app.services.system_service.platform')
@patch('backend.app.services.system_service.subprocess.Popen')
def test_open_calculator_linux(mock_popen, mock_platform, system_service):
    # Arrange
    mock_platform.system.return_value = "Linux"
    
    # Act
    result = system_service.open_calculator()
    
    # Assert
    assert result.get("status") == "success"
    assert "Abrindo 'calculadora'" in result.get("message")
    mock_popen.assert_called_once_with(["gnome-calculator"]) # Ou qual for o comando no seu apps_config
    mock_platform.system.assert_called_once()


# --- Testes para _interpret_timer_duration (exemplo de teste de método privado, se necessário) ---
# Geralmente testamos métodos públicos, mas se um privado tem lógica complexa, pode valer a pena
def test_interpret_timer_duration_seconds(system_service):
    assert system_service._interpret_timer_duration("10 segundos") == 10
    assert system_service._interpret_timer_duration("10") == 10 # Assumindo que sem unidade é segundos

def test_interpret_timer_duration_minutes(system_service):
    assert system_service._interpret_timer_duration("2 minutos") == 120

def test_interpret_timer_duration_hours(system_service):
    assert system_service._interpret_timer_duration("1 hora") == 3600

def test_interpret_timer_duration_invalid(system_service):
    assert system_service._interpret_timer_duration("dez minutos") is None # Não lida com extenso ainda
    assert system_service._interpret_timer_duration("abc") is None

# Você continuaria adicionando testes para search_web, start_timer (mockando threading e pygame),
# adjust_system_volume (mockando pycaw se não disponível no ambiente de teste), etc.