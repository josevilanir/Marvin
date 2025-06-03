# backend/tests/test_system_service.py
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime # <--- CORREÇÃO 1: Importar datetime

# Importe a classe que você quer testar
# Assumindo que pytest.ini tem "pythonpath = . backend" e você está rodando da raiz do projeto
from app.services.system_service import SystemService
# from backend.app.core.config_manager import ConfigManager # Não precisamos do real para estes testes
# from backend.app.core.constants import RESOURCE_PATH # Não precisamos do real para estes testes

# Criar um DummyConfigManager para não depender do real ConfigManager nos testes unitários
class DummyConfigManager:
    pass

@pytest.fixture
def system_service():
    """Retorna uma instância de SystemService com um ConfigManager dummy."""
    dummy_config = DummyConfigManager()
    service = SystemService(config_manager=dummy_config)
    return service

# --- Testes para get_current_datetime_string ---
def test_get_current_datetime_string_returns_dict_with_status_success(system_service):
    result = system_service.get_current_datetime_string()
    assert isinstance(result, dict)
    assert result.get("status") == "success"

@patch('app.services.system_service.datetime') # CORREÇÃO 3: Caminho completo para datetime DENTRO do módulo system_service
def test_get_current_datetime_string_formats_message_correctly(mock_datetime_module, system_service):
    # Arrange: Configure o mock para retornar uma data/hora específica
    fixed_now = datetime(2024, 5, 28, 10, 30, 0) # 28 de Maio de 2024, 10:30:00
    mock_datetime_module.now.return_value = fixed_now # Mockar datetime.now()
    
    # Act
    result = system_service.get_current_datetime_string()
    
    # Assert
    # Ajuste o formato da data para corresponder ao seu locale, especialmente o mês.
    # Se o seu sistema estiver em português, "May" será "maio".
    # Para tornar o teste independente de locale, você pode mockar o strftime ou comparar partes.
    # Por simplicidade, vamos assumir que o strftime produzirá o mês em português no ambiente de teste.
    # Se o locale for US English, seria "May". Se for pt_BR, "maio".
    # O seu system_service.py usa '%B', que é locale-dependent.
    # Para um teste robusto, é melhor não depender do resultado exato de %B ou mockar strftime.
    # Mas, para agora, vamos usar o que sua função produz.
    # A função está produzindo: "Hoje é dia %d de %B de %Y."
    
    # Gerar a data esperada usando a mesma lógica (ou mockar strftime)
    expected_time_string = fixed_now.strftime("São %H horas e %M minutos.")
    # Para %B, precisamos ter cuidado com o locale. Vamos testar o que a função retornaria:
    # Para evitar problemas com locale em diferentes sistemas de CI/desenvolvimento,
    # é melhor testar o formato sem depender da string exata do mês, ou mockar strftime.
    # Mas vamos tentar replicar o formato do seu código:
    # Em vez de depender do nome do mês, vamos apenas verificar se o dia e ano estão corretos e a estrutura geral.
    
    assert result.get("time") == expected_time_string
    assert fixed_now.strftime("Hoje é dia %d de") in result.get("date") # Verifica parte da data
    assert str(fixed_now.year) in result.get("date") # Verifica ano

    # Para uma verificação mais precisa da mensagem completa, se o locale do mês for um problema:
    # expected_date_string_prefix = fixed_now.strftime("Hoje é dia %d de ")
    # expected_date_string_suffix = fixed_now.strftime(" de %Y.")
    # assert result.get("message").startswith(f"{expected_time_string} {expected_date_string_prefix}")
    # assert result.get("message").endswith(expected_date_string_suffix)
    
    # Verificação da mensagem completa (assumindo que %B produz algo)
    # Se o locale for um problema, este assert pode ser instável.
    expected_date_string = fixed_now.strftime("Hoje é dia %d de %B de %Y.")
    assert result.get("message") == f"{expected_time_string} {expected_date_string}"
    
    mock_datetime_module.now.assert_called_once()

# --- Testes para get_marvin_info ---
def test_get_marvin_info_returns_expected_message(system_service):
    result = system_service.get_marvin_info()
    assert result.get("status") == "success"
    assert "Eu sou Marvin" in result.get("message")

# --- Testes para open_calculator ---
# CORREÇÃO 2: Caminho completo para os mocks de platform e subprocess.Popen DENTRO do módulo system_service
@patch('app.services.system_service.platform')
@patch('app.services.system_service.subprocess.Popen')
def test_open_calculator_windows(mock_popen, mock_platform_module, system_service):
    # Arrange
    mock_platform_module.system.return_value = "windows" # Simula estar no Windows
    
    # Act
    result = system_service.open_calculator() # open_calculator chama open_application
    
    # Assert
    assert result.get("status") == "success"
    assert "Abrindo 'calculadora'" in result.get("message")
    # No seu SystemService, para windows e "calc.exe", você usa shell=True
    mock_popen.assert_called_once_with(["calc.exe"], shell=True)
    mock_platform_module.system.assert_called_once()

@patch('app.services.system_service.platform')
@patch('app.services.system_service.subprocess.Popen')
def test_open_calculator_linux(mock_popen, mock_platform_module, system_service):
    # Arrange
    mock_platform_module.system.return_value = "linux"
    
    # Act
    result = system_service.open_calculator() # open_calculator chama open_application

    # Assert
    assert result.get("status") == "success"
    assert "Abrindo 'calculadora'" in result.get("message")
    # No seu SystemService, para linux e "gnome-calculator", você NÃO usa shell=True
    mock_popen.assert_called_once_with(["gnome-calculator"])
    mock_platform_module.system.assert_called_once() # Deve ser chamado dentro de open_application

# --- Testes para _interpret_timer_duration ---
# (Estes testes para métodos privados são opcionais, mas podem ser úteis)
def test_interpret_timer_duration_seconds(system_service):
    assert system_service._interpret_timer_duration("10 segundos") == 10
    assert system_service._interpret_timer_duration("10") == 10 

def test_interpret_timer_duration_minutes(system_service):
    assert system_service._interpret_timer_duration("2 minutos") == 120

def test_interpret_timer_duration_hours(system_service):
    assert system_service._interpret_timer_duration("1 hora") == 3600

def test_interpret_timer_duration_invalid(system_service):
    assert system_service._interpret_timer_duration("dez minutos") is None 
    assert system_service._interpret_timer_duration("abc") is None

# Adicione mais testes aqui para:
# - open_application com diferentes cenários (app não encontrado, outro OS)
# - search_web (mockando webbrowser.open)
# - start_timer (mockando threading.Thread e pygame.mixer)
# - adjust_system_volume (mockando PYCAW_AVAILABLE e as chamadas da pycaw)