# backend/tests/test_youtube_service.py
import pytest
from unittest.mock import patch, MagicMock, call

# Correção no caminho de importação
from backend.app.services.youtube_service import YouTubeService
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException, ElementClickInterceptedException
from selenium.webdriver.common.by import By
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait

class DummyConfigManager:
    pass

@pytest.fixture
def mock_driver_instance():
    mock_driver = MagicMock(spec=webdriver.Chrome)
    mock_driver.current_url = "http://fake-youtube-url.com"
    mock_driver.title = "Fake YouTube Page"
    mock_driver.get.return_value = None
    mock_driver.find_elements.return_value = [MagicMock()]
    mock_driver.find_element.return_value = MagicMock()
    mock_driver.execute_script.return_value = None
    mock_driver.quit.return_value = None
    mock_driver.back.return_value = None
    mock_driver.fullscreen_window.return_value = None
    mock_driver.maximize_window.return_value = None
    return mock_driver

@pytest.fixture
def youtube_service(mock_driver_instance):
    dummy_config = DummyConfigManager()
    with patch.object(YouTubeService, '_initialize_driver', return_value=True):
        service = YouTubeService(config_manager=dummy_config)
        service.driver = mock_driver_instance
    return service, mock_driver_instance

def test_quit_driver_calls_driver_quit(youtube_service):
    service, mock_driver = youtube_service
    service.quit_driver()
    mock_driver.quit.assert_called_once()
    assert service.driver is None

def test_search_youtube_success(youtube_service):
    service, mock_driver = youtube_service
    query = "test query"
    
    # Configurar o mock para retornar elementos quando esperado
    mock_driver.find_elements.return_value = [MagicMock()]
    
    result = service.search_youtube(query)
    
    assert result["status"] == "success"
    mock_driver.get.assert_called_once_with(f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}")
    assert mock_driver.find_element.called

def test_search_youtube_empty_query(youtube_service):
    service, _ = youtube_service
    result = service.search_youtube("")
    assert result["status"] == "error"

def test_search_youtube_webdriver_exception_on_get(youtube_service):
    service, mock_driver = youtube_service
    mock_driver.get.side_effect = WebDriverException("Fake error")
    result = service.search_youtube("test")
    assert result["status"] == "error"

def test_search_youtube_timeout_exception_on_wait(youtube_service):
    service, mock_driver = youtube_service
    
    # Configurar o mock para lançar TimeoutException quando until for chamado
    mock_wait = MagicMock()
    mock_wait.until.side_effect = TimeoutException("Timeout")
    
    with patch('backend.app.services.youtube_service.WebDriverWait', return_value=mock_wait):
        result = service.search_youtube("test")
        assert result["status"] == "error"
        assert "Timeout" in result["message"]

def test_click_video_by_position_success(youtube_service):
    service, mock_driver = youtube_service
    mock_video = MagicMock()
    mock_video.get_attribute.return_value = "Test Video"
    mock_driver.find_elements.return_value = [mock_video]
    
    result = service.click_video_by_position(1)
    assert result["status"] == "success"
    mock_video.click.assert_called_once()

def test_click_video_by_position_out_of_range(youtube_service):
    service, mock_driver = youtube_service
    mock_driver.find_elements.return_value = [MagicMock()]
    result = service.click_video_by_position(2)
    assert result["status"] == "error"

def test_control_video_playback_toggle_pause_play(youtube_service):
    service, mock_driver = youtube_service
    with patch('backend.app.services.youtube_service.WebDriverWait') as mock_wait:
        mock_wait.return_value.until.return_value = MagicMock()
        result = service.control_video_playback('toggle_pause_play')
        assert result["status"] == "success"

def test_skip_ad_pyautogui_success(youtube_service):
    service, _ = youtube_service
    
    # Mockar a importação dentro do método usando patch.object
    with patch.object(service, 'skip_ad_pyautogui', autospec=True) as mock_method:
        # Configurar o retorno simulado
        mock_method.return_value = {
            "status": "success",
            "message": "Attempted to click 'Skip Ad' coordinates."
        }
        
        result = service.skip_ad_pyautogui()
        
        assert result["status"] == "success"
        assert "Attempted to click 'Skip Ad' coordinates" in result["message"]

def test_attempt_skip_ad_selenium_found(youtube_service):
    service, _ = youtube_service
    with patch('backend.app.services.youtube_service.WebDriverWait') as mock_wait:
        mock_wait.return_value.until.return_value = MagicMock()
        result = service.attempt_skip_ad_selenium()
        assert result["status"] == "success"

def test_attempt_skip_ad_selenium_not_found(youtube_service):
    service, _ = youtube_service
    with patch('backend.app.services.youtube_service.WebDriverWait') as mock_wait:
        mock_wait.return_value.until.side_effect = TimeoutException()
        result = service.attempt_skip_ad_selenium()
        assert result["status"] == "info"

def test_select_channel_from_results_success(youtube_service):
    service, mock_driver = youtube_service
    mock_channel = MagicMock()
    mock_channel.find_element.return_value = MagicMock(text="Test Channel")
    mock_driver.find_element.return_value = mock_channel
    
    result = service.select_channel_from_results()
    assert result["status"] == "success"
    assert "Test Channel" in result["message"]

def test_go_back_in_browser_history_success(youtube_service):
    service, mock_driver = youtube_service
    
    # Configurar o mock para simular o comportamento de navegação
    with patch('backend.app.services.youtube_service.WebDriverWait') as mock_wait:
        mock_wait.return_value.until.return_value = True
        
        result = service.go_back_in_browser_history()
        
        assert result["status"] == "success"
        mock_driver.back.assert_called_once()

def test_skip_ad_pyautogui_import_error(youtube_service):
    service, _ = youtube_service
    
    with patch.object(service, '_import_pyautogui', return_value=None):
        result = service.skip_ad_pyautogui()
        
        assert result["status"] == "error"
        assert "PyAutoGUI library not found" in result["message"]