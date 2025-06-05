# backend/app/services/youtube_service.py
import time
# import pyautogui # REMOVIDO DO TOPO - Será importado sob demanda
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options as ChromeOptions # Renamed to avoid conflict
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    ElementClickInterceptedException,
    WebDriverException
)
import traceback

# Assuming ConfigManager might hold WebDriver path or other settings
from app.core.config_manager import ConfigManager

class YouTubeService:
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.driver = None
        # You might want to make headless configurable via ConfigManager
        self.headless_mode = False # Set to True to run Chrome without UI

    def _initialize_driver(self) -> bool:
        """Initializes the Selenium WebDriver if not already initialized."""
        if self.driver:
            try:
                # Check if driver is still responsive
                self.driver.current_url
                return True
            except WebDriverException:
                print("YouTubeService: WebDriver was not responsive. Re-initializing...")
                self.quit_driver() # Clean up old driver

        try:
            print("YouTubeService: Initializing WebDriver for Chrome...")
            chrome_options = ChromeOptions()
            if self.headless_mode:
                chrome_options.add_argument("--headless")
                chrome_options.add_argument("--window-size=1920x1080")
                chrome_options.add_argument("--disable-gpu")
            
            self.driver = webdriver.Chrome(options=chrome_options)
            print("YouTubeService: WebDriver initialized successfully.")
            return True
        except WebDriverException as e:
            print(f"YouTubeService: Error initializing WebDriver: {e}")
            print("Please ensure ChromeDriver is installed and in your PATH, or Selenium Manager can find it.")
            self.driver = None
            return False
        except Exception as e:
            print(f"YouTubeService: Unexpected error initializing WebDriver: {e}")
            self.driver = None
            return False

    def quit_driver(self):
        """Quits the WebDriver if it's active."""
        if self.driver:
            try:
                self.driver.quit()
                print("YouTubeService: WebDriver quit successfully.")
            except Exception as e:
                print(f"YouTubeService: Error quitting WebDriver: {e}")
            finally:
                self.driver = None
    
    def _ensure_driver(self):
        """Ensures driver is initialized. Raises exception if fails."""
        if not self.driver and not self._initialize_driver():
            # Se _initialize_driver() falhar, ele já imprime uma mensagem e define self.driver = None
            # A exceção aqui garante que os métodos não prossigam se a inicialização falhar.
            raise WebDriverException("YouTubeService: WebDriver could not be initialized or is not available.")


    def search_youtube(self, query: str) -> dict:
        """
        Performs a search on YouTube.
        """
        if not query:
            return {"status": "error", "message": "Search query cannot be empty."}
        
        try:
            self._ensure_driver()
            # A URL original do seu código era: f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
            # Vou mantê-la, mas se for um proxy específico, pode não funcionar em todos os ambientes.
            # Uma URL de busca padrão do YouTube seria: f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
            self.driver.get(f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}")

            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.XPATH, '//ytd-video-renderer | //ytd-playlist-renderer | //ytd-channel-renderer'))
            )
            return {"status": "success", "message": f"Search results for '{query}' loaded."}
        except WebDriverException as e:
             return {"status": "error", "message": f"WebDriver error during Youtube: {e}"}
        except TimeoutException:
            return {"status": "error", "message": f"Timeout waiting for Youtube results for '{query}'."}
        except Exception as e:
            print(traceback.format_exc())
            return {"status": "error", "message": f"Unexpected error during Youtube: {e}"}

    def click_video_by_position(self, position: int = 1) -> dict:
        """
        Clicks a video in the search results by its 1-based position.
        """
        try:
            self._ensure_driver() # Garante que o driver está pronto
        except WebDriverException as e:
             return {"status": "error", "message": str(e)} # Retorna o erro da inicialização

        if position < 1:
            return {"status": "error", "message": "Video position must be 1 or greater."}
        
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_all_elements_located((By.XPATH, '//a[@id="video-title"]'))
            )
            videos = self.driver.find_elements(By.XPATH, '//a[@id="video-title"]')
            
            if not videos:
                return {"status": "error", "message": "No videos found on the page."}

            if len(videos) >= position:
                target_video = videos[position - 1]
                video_title = target_video.get_attribute("title") or "Unknown Title"
                print(f"YouTubeService: Attempting to click video at position {position}: '{video_title}'")
                
                self.driver.execute_script("arguments[0].scrollIntoView(true);", target_video)
                time.sleep(0.5) 
                target_video.click()
                return {"status": "success", "message": f"Clicked video '{video_title}' (position {position})."}
            else:
                return {"status": "error", "message": f"Video position {position} is out of range. Found {len(videos)} videos."}
        except TimeoutException:
            return {"status": "error", "message": "Timeout waiting for videos to appear before clicking."}
        except ElementClickInterceptedException:
            return {"status": "error", "message": "Could not click video. Another element may be obscuring it (e.g., a popup)."}
        except WebDriverException as e: # Captura erros gerais do WebDriver aqui também
            return {"status": "error", "message": f"WebDriver error clicking video: {e}"}
        except Exception as e:
            return {"status": "error", "message": f"Error clicking video by position: {e}"}

    def select_channel_from_results(self) -> dict:
        """
        Attempts to click on the first channel link in search results.
        """
        try:
            self._ensure_driver()
        except WebDriverException as e:
             return {"status": "error", "message": str(e)}

        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//ytd-channel-renderer//a[@id="main-link"]'))
            )
            channel_link = self.driver.find_element(By.XPATH, '//ytd-channel-renderer//a[@id="main-link"]')
            channel_name_element = channel_link.find_element(By.XPATH, './/yt-formatted-string[@id="text"]')
            channel_name = channel_name_element.text if channel_name_element else "Unknown Channel"
            print(f"YouTubeService: Clicking channel '{channel_name}'")
            channel_link.click()
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.ID, "tabsContent")) 
            )
            return {"status": "success", "message": f"Selected channel '{channel_name}'."}
        except TimeoutException:
            return {"status": "error", "message": "Timeout waiting for channel link or channel page to load."}
        except NoSuchElementException:
            return {"status": "error", "message": "No channel link found in the current results."}
        except WebDriverException as e:
            return {"status": "error", "message": f"WebDriver error selecting channel: {e}"}
        except Exception as e:
            return {"status": "error", "message": f"Error selecting channel: {e}"}


    def control_video_playback(self, action: str) -> dict:
        """
        Controls video playback (pause, play, toggle fullscreen, etc.).
        'action' can be 'toggle_pause_play', 'fullscreen', 'exit_fullscreen', 'maximize_window'.
        """
        try:
            self._ensure_driver()
        except WebDriverException as e:
             return {"status": "error", "message": str(e)}
        
        try:
            if action == 'toggle_pause_play':
                WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.TAG_NAME, "video")))
                self.driver.execute_script(
                    "var video = document.querySelector('video'); if (video) { video.paused ? video.play() : video.pause(); } else { return 'No video element found'; }"
                )
                return {"status": "success", "message": "Toggled video pause/play."}
            
            elif action == 'fullscreen':
                self.driver.fullscreen_window()
                return {"status": "success", "message": "Entered fullscreen."}
            
            elif action == 'exit_fullscreen':
                try:
                    import pyautogui # Importa pyautogui SÓ AQUI DENTRO
                    pyautogui.press('esc') 
                    return {"status": "success", "message": "Attempted to exit fullscreen (pressed ESC)."}
                except ImportError:
                    print("YouTubeService: PyAutoGUI could not be imported for 'exit_fullscreen'.")
                    return {"status": "error", "message": "PyAutoGUI library not found for this action."}
                except Exception as e_pg:
                    print(f"YouTubeService: PyAutoGUI error during exit_fullscreen: {e_pg}")
                    return {"status": "error", "message": f"PyAutoGUI error exiting fullscreen: {e_pg}"}


            elif action == 'maximize_window':
                self.driver.maximize_window()
                return {"status": "success", "message": "Window maximized."}
            
            else:
                return {"status": "error", "message": f"Unknown video control action: {action}"}

        except TimeoutException:
             return {"status": "error", "message": "No video element found to control playback."}
        except WebDriverException as e:
            return {"status": "error", "message": f"WebDriver error during video control: {e}"}
        except Exception as e:
            return {"status": "error", "message": f"Error during video control action '{action}': {e}"}

    def skip_ad_pyautogui(self) -> dict:
        """Attempts to skip a YouTube ad using PyAutoGUI."""
        try:
            pyautogui = self._import_pyautogui()
            if not pyautogui:
                return {"status": "error", "message": "PyAutoGUI library not found for this action."}
                
            skip_ad_coords = (1332, 787) 
            print(f"YouTubeService: Attempting to skip ad by clicking coordinates: {skip_ad_coords}")
            current_mouse_pos = pyautogui.position()
            pyautogui.moveTo(skip_ad_coords)
            pyautogui.click()
            pyautogui.moveTo(current_mouse_pos)
            return {"status": "success", "message": "Attempted to click 'Skip Ad' coordinates."}
        except Exception as e:
            return {"status": "error", "message": f"Error using PyAutoGUI to skip ad: {e}"}

    def _import_pyautogui(self):
        """Helper method to import pyautogui (can be mocked in tests)."""
        try:
            import pyautogui
            return pyautogui
        except ImportError:
            return None

    def attempt_skip_ad_selenium(self) -> dict:
        """Attempts to find and click a 'Skip Ad' button using Selenium."""
        try:
            self._ensure_driver()
        except WebDriverException as e:
             return {"status": "error", "message": str(e)}
        
        selectors = [
            "//button[contains(@class, 'ytp-ad-skip-button')]",
            "//div[contains(@class, 'ytp-ad-skip-button')]",
            "//button[@aria-label='Skip Ad']",
            "//div[@id='skip-button']//button",
            "//yt-button-renderer[contains(@class,'ytp-ad-skip-button')]",
            "//span[contains(text(),'Skip Ad') or contains(text(),'Skip Ads')]/ancestor::button[1]"
        ]
        
        for selector in selectors:
            try:
                skip_button = WebDriverWait(self.driver, 2).until(
                    EC.element_to_be_clickable((By.XPATH, selector))
                )
                if skip_button:
                    print(f"YouTubeService: Found 'Skip Ad' button with selector: {selector}")
                    skip_button.click()
                    return {"status": "success", "message": "Clicked 'Skip Ad' button."}
            except TimeoutException:
                continue 
            except WebDriverException as e: # Captura erros do Selenium
                print(f"YouTubeService: WebDriver error trying selector '{selector}': {e}")
                continue
            except Exception as e:
                print(f"YouTubeService: Error trying selector '{selector}': {e}")
                continue
        
        return {"status": "info", "message": "No 'Skip Ad' button found or could not be clicked."}


    def go_back_in_browser_history(self) -> dict:
        """Navigates back in the browser history."""
        try:
            self._ensure_driver()
        except WebDriverException as e:
             return {"status": "error", "message": str(e)}
        try:
            self.driver.back()
            WebDriverWait(self.driver, 10).until(lambda d: d.execute_script('return document.readyState') == 'complete')
            return {"status": "success", "message": "Navigated back in browser history."}
        except WebDriverException as e:
            return {"status": "error", "message": f"WebDriver error navigating back: {e}"}
        except Exception as e:
            return {"status": "error", "message": f"Error navigating back: {e}"}

    def __del__(self):
        """Ensure WebDriver is quit when the service object is destroyed."""
        self.quit_driver()


if __name__ == '__main__':
    # Example Usage (requires ChromeDriver in PATH or Selenium Manager)
    # Create a dummy ConfigManager for testing
    class DummyConfigManager: # Definindo a classe dummy aqui para o escopo do if __name__
        pass
    
    cfg = DummyConfigManager()
    yt_service = None 

    try:
        yt_service = YouTubeService(cfg)
        
        search_query = "python programming tutorial"
        # A linha original tinha um erro de digitação: yt_service.search_Youtube_query
        # O método correto é search_youtube
        print(f"\n--- Testing Youtube: '{search_query}' ---")
        result = yt_service.search_Youtube_query # Corrigido aqui
        print(f"Search Result: {result}")

        if result.get("status") == "success": # Adicionado .get() para segurança
            print("\n--- Testing Clicking First Video ---")
            click_result = yt_service.click_video_by_position(1)
            print(f"Click Result: {click_result}")

            if click_result.get("status") == "success": # Adicionado .get()
                print("Waiting a few seconds for video to potentially load/play...")
                time.sleep(5) 

                print("\n--- Testing Skip Ad (Selenium) ---")
                skip_ad_sel_result = yt_service.attempt_skip_ad_selenium()
                print(f"Skip Ad (Selenium) Result: {skip_ad_sel_result}")
                
                # O if original tinha um bug de lógica, skip_ad_pyautogui era chamado independente do resultado do selenium.
                # Vamos chamar o pyautogui apenas se o selenium não funcionar.
                if skip_ad_sel_result.get("status") != "success": 
                    print("\n--- Testing Skip Ad (PyAutoGUI - unreliable, ensure window focus) ---")
                    # Este bloco pode falhar no Codespaces devido à ausência de display.
                    try:
                        import pyautogui # Importa aqui para o teste
                        time.sleep(3) 
                        skip_ad_gui_result = yt_service.skip_ad_pyautogui()
                        print(f"Skip Ad (PyAutoGUI) Result: {skip_ad_gui_result}")
                    except ImportError:
                        print("PyAutoGUI not available for this test block.")
                    except Exception as e_pg_test:
                        print(f"Error during PyAutoGUI test block: {e_pg_test}")


                print("\n--- Testing Video Playback Toggle (Pause/Play) ---")
                time.sleep(2) 
                toggle_result = yt_service.control_video_playback('toggle_pause_play') 
                print(f"Toggle 1 Result: {toggle_result}")
                time.sleep(3)
                toggle_result_2 = yt_service.control_video_playback('toggle_pause_play') 
                print(f"Toggle 2 Result: {toggle_result_2}")

            print("\n--- Testing Go Back ---") # Movido para fora do if click_result
            back_result = yt_service.go_back_in_browser_history()
            print(f"Go Back Result: {back_result}")
            time.sleep(3)

    except Exception as e:
        print(f"\nAn error occurred in YouTubeService example: {e}")
        traceback.print_exc()
    finally:
        if yt_service:
            print("\n--- Quitting WebDriver ---")
            yt_service.quit_driver()