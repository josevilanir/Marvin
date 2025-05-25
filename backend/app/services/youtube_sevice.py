# backend/app/services/youtube_service.py
import time
import pyautogui # For skipping ads, exiting fullscreen
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
                chrome_options.add_argument("--window-size=1920x1080") # Recommended for headless
                chrome_options.add_argument("--disable-gpu") # Often necessary for headless
            
            # Add other options if needed, e.g., user-agent, proxy
            # chrome_options.add_argument("user-data-dir=path/to/your/chrome/profile") # For persistent login (use with caution)

            # Path to chromedriver can be handled by Selenium Manager (Selenium 4.6+)
            # or specified explicitly if needed:
            # self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
            # For simplicity, relying on Selenium Manager or chromedriver in PATH
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
            raise WebDriverException("YouTubeService: WebDriver could not be initialized.")


    def search_youtube(self, query: str) -> dict:
        """
        Performs a search on YouTube.
        Based on pesquisar_youtube_chrome from
        """
        if not query:
            return {"status": "error", "message": "Search query cannot be empty."}
        
        try:
            self._ensure_driver()
            # Original URL: 'https://www.youtube.com'
            # This seems like a proxy or a specific setup. For general use, direct YouTube URL is better.
            # Let's use the direct YouTube URL. If the googleusercontent URL is required for a specific
            # environment (like a sandboxed iframe), this might need to be configurable.
            self.driver.get(f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}")

            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.XPATH, '//ytd-video-renderer | //ytd-playlist-renderer | //ytd-channel-renderer'))
            )
            return {"status": "success", "message": f"Search results for '{query}' loaded."}
        except WebDriverException as e: # Covers issues like no internet, driver crashes
             return {"status": "error", "message": f"WebDriver error during Youtube: {e}"}
        except TimeoutException:
            return {"status": "error", "message": f"Timeout waiting for Youtube results for '{query}'."}
        except Exception as e:
            print(traceback.format_exc())
            return {"status": "error", "message": f"Unexpected error during Youtube: {e}"}

    def click_video_by_position(self, position: int = 1) -> dict:
        """
        Clicks a video in the search results by its 1-based position.
        Based on clicar_video from
        """
        if not self.driver:
            return {"status": "error", "message": "WebDriver not initialized. Perform a search first."}
        if position < 1:
            return {"status": "error", "message": "Video position must be 1 or greater."}
        
        try:
            # Wait for video titles to be present
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_all_elements_located((By.XPATH, '//a[@id="video-title"]'))
            )
            videos = self.driver.find_elements(By.XPATH, '//a[@id="video-title"]') # Finds videos and playlist titles
            
            if not videos:
                return {"status": "error", "message": "No videos found on the page."}

            if len(videos) >= position:
                target_video = videos[position - 1]
                video_title = target_video.get_attribute("title") or "Unknown Title"
                print(f"YouTubeService: Attempting to click video at position {position}: '{video_title}'")
                
                # Scroll into view and click
                self.driver.execute_script("arguments[0].scrollIntoView(true);", target_video)
                time.sleep(0.5) # Brief pause for scrolling
                target_video.click()
                return {"status": "success", "message": f"Clicked video '{video_title}' (position {position})."}
            else:
                return {"status": "error", "message": f"Video position {position} is out of range. Found {len(videos)} videos."}
        except TimeoutException:
            return {"status": "error", "message": "Timeout waiting for videos to appear before clicking."}
        except ElementClickInterceptedException:
            return {"status": "error", "message": "Could not click video. Another element may be obscuring it (e.g., a popup)."}
        except Exception as e:
            return {"status": "error", "message": f"Error clicking video by position: {e}"}

    def select_channel_from_results(self) -> dict:
        """
        Attempts to click on the first channel link in search results.
        Based on selecionar_canal from
        """
        if not self.driver:
            return {"status": "error", "message": "WebDriver not initialized."}
        try:
            # Wait for channel renderer to be present
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//ytd-channel-renderer//a[@id="main-link"]'))
            )
            channel_link = self.driver.find_element(By.XPATH, '//ytd-channel-renderer//a[@id="main-link"]')
            channel_name = channel_link.find_element(By.XPATH, './/yt-formatted-string[@id="text"]').text
            print(f"YouTubeService: Clicking channel '{channel_name}'")
            channel_link.click()
            # Wait for channel page to load (e.g., by checking for channel header or specific tab)
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.ID, "tabsContent")) # Common element on channel pages
            )
            return {"status": "success", "message": f"Selected channel '{channel_name}'."}
        except TimeoutException:
            return {"status": "error", "message": "Timeout waiting for channel link or channel page to load."}
        except NoSuchElementException:
            return {"status": "error", "message": "No channel link found in the current results."}
        except Exception as e:
            return {"status": "error", "message": f"Error selecting channel: {e}"}


    def control_video_playback(self, action: str) -> dict:
        """
        Controls video playback (pause, play, toggle fullscreen, etc.).
        'action' can be 'toggle_pause_play', 'fullscreen', 'exit_fullscreen', 'maximize_window'.
        Based on pausar_retornar_video, tela_cheia_chrome, sair_tela_cheia, maximizar_janela
        from
        """
        if not self.driver:
            return {"status": "error", "message": "WebDriver not initialized."}
        
        try:
            if action == 'toggle_pause_play':
                # Check if a video element is present and interactable
                WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.TAG_NAME, "video")))
                self.driver.execute_script(
                    "var video = document.querySelector('video'); if (video) { video.paused ? video.play() : video.pause(); } else { return 'No video element found'; }"
                )
                # To get actual state, we'd need to query:
                # is_paused = self.driver.execute_script("return document.querySelector('video').paused;")
                # message = "Video paused." if is_paused else "Video playing."
                return {"status": "success", "message": "Toggled video pause/play."}
            
            elif action == 'fullscreen':
                self.driver.fullscreen_window()
                return {"status": "success", "message": "Entered fullscreen."}
            
            elif action == 'exit_fullscreen':
                # Selenium doesn't have a direct "exit fullscreen" if entered via browser controls.
                # PyAutoGUI is a more reliable way for this if the window has focus.
                # For windowed fullscreen (driver.fullscreen_window()), F11 or ESC might work.
                # This assumes the browser window has focus.
                pyautogui.press('esc') 
                # Alternatively, if you want to ensure it's not fullscreen by Selenium's definition:
                # self.driver.maximize_window() # Or set_window_size to a normal size
                return {"status": "success", "message": "Attempted to exit fullscreen (pressed ESC)."}

            elif action == 'maximize_window':
                self.driver.maximize_window()
                return {"status": "success", "message": "Window maximized."}
            
            else:
                return {"status": "error", "message": f"Unknown video control action: {action}"}

        except TimeoutException:
             return {"status": "error", "message": "No video element found to control playback."}
        except Exception as e:
            return {"status": "error", "message": f"Error during video control action '{action}': {e}"}

    def skip_ad_pyautogui(self) -> dict:
        """
        Attempts to skip a YouTube ad using PyAutoGUI by clicking a predefined coordinate.
        Based on Pular_Anuncio from
        WARNING: This is highly unreliable and depends on screen resolution, ad layout, etc.
        A better approach is to use Selenium to find and click the "Skip Ad" button if possible.
        """
        # Original coordinates: (1332, 787)
        # This should be made configurable if used.
        skip_ad_coords = (1332, 787) 
        try:
            print(f"YouTubeService: Attempting to skip ad by clicking coordinates: {skip_ad_coords}")
            current_mouse_pos = pyautogui.position()
            pyautogui.moveTo(skip_ad_coords)
            pyautogui.click()
            pyautogui.moveTo(current_mouse_pos) # Move mouse back
            return {"status": "success", "message": "Attempted to click 'Skip Ad' coordinates."}
        except Exception as e:
            # PyAutoGUI might fail if it can't control the mouse (e.g., on some Linux display servers without setup)
            return {"status": "error", "message": f"Error using PyAutoGUI to skip ad: {e}"}

    def attempt_skip_ad_selenium(self) -> dict:
        """Attempts to find and click a 'Skip Ad' button using Selenium."""
        if not self.driver:
            return {"status": "error", "message": "WebDriver not initialized."}
        
        # Common selectors for skip ad buttons (these can change frequently)
        selectors = [
            "//button[contains(@class, 'ytp-ad-skip-button')]", # Standard button
            "//div[contains(@class, 'ytp-ad-skip-button')]",   # Sometimes it's a div
            "//button[@aria-label='Skip Ad']",
            "//div[@id='skip-button']//button",
            "//yt-button-renderer[contains(@class,'ytp-ad-skip-button')]",
            "//span[contains(text(),'Skip Ad') or contains(text(),'Skip Ads')]/ancestor::button[1]"
        ]
        
        for selector in selectors:
            try:
                skip_button = WebDriverWait(self.driver, 2).until( # Short wait, ad buttons appear quickly
                    EC.element_to_be_clickable((By.XPATH, selector))
                )
                if skip_button:
                    print(f"YouTubeService: Found 'Skip Ad' button with selector: {selector}")
                    skip_button.click()
                    return {"status": "success", "message": "Clicked 'Skip Ad' button."}
            except TimeoutException:
                continue # Try next selector
            except Exception as e:
                print(f"YouTubeService: Error trying selector '{selector}': {e}")
                continue
        
        return {"status": "info", "message": "No 'Skip Ad' button found or could not be clicked."}


    def go_back_in_browser_history(self) -> dict:
        """Navigates back in the browser history."""
        if not self.driver:
            return {"status": "error", "message": "WebDriver not initialized."}
        try:
            self.driver.back()
            # Wait for page to potentially reload
            WebDriverWait(self.driver, 10).until(lambda d: d.execute_script('return document.readyState') == 'complete')
            return {"status": "success", "message": "Navigated back in browser history."}
        except Exception as e:
            return {"status": "error", "message": f"Error navigating back: {e}"}

    # The functions clicar_video_canal and clicar_video_canal_in were complex and
    # highly dependent on specific YouTube page structures.
    # A more generic "click element by text/xpath" might be more maintainable if needed.
    # For now, focusing on the core functionalities.

    def __del__(self):
        """Ensure WebDriver is quit when the service object is destroyed."""
        self.quit_driver()


if __name__ == '__main__':
    # Example Usage (requires ChromeDriver in PATH or Selenium Manager)
    # Create a dummy ConfigManager for testing
    class DummyConfigManager:
        pass
    
    cfg = DummyConfigManager()
    yt_service = None # Initialize to None

    try:
        yt_service = YouTubeService(cfg)
        
        # Test search
        search_query = "python programming tutorial"
        print(f"\n--- Testing Youtube: '{search_query}' ---")
        result = yt_service.search_Youtube_query
        print(f"Search Result: {result}")

        if result["status"] == "success":
            # Test clicking first video
            print("\n--- Testing Clicking First Video ---")
            click_result = yt_service.click_video_by_position(1)
            print(f"Click Result: {click_result}")

            if click_result["status"] == "success":
                print("Waiting a few seconds for video to potentially load/play...")
                time.sleep(5) # Allow time for page navigation and video to start

                print("\n--- Testing Skip Ad (Selenium) ---")
                skip_ad_sel_result = yt_service.attempt_skip_ad_selenium()
                print(f"Skip Ad (Selenium) Result: {skip_ad_sel_result}")
                if skip_ad_sel_result["status"] != "success": # If Selenium didn't find it, try PyAutoGUI as a fallback
                    print("\n--- Testing Skip Ad (PyAutoGUI - unreliable, ensure window focus) ---")
                    # Make sure the browser window is active and focused before this runs for PyAutoGUI
                    time.sleep(3) # Give user time to focus the window
                    skip_ad_gui_result = yt_service.skip_ad_pyautogui()
                    print(f"Skip Ad (PyAutoGUI) Result: {skip_ad_gui_result}")


                print("\n--- Testing Video Playback Toggle (Pause/Play) ---")
                time.sleep(2) # Wait a bit
                toggle_result = yt_service.control_video_playback('toggle_pause_play') # Should pause
                print(f"Toggle 1 Result: {toggle_result}")
                time.sleep(3)
                toggle_result_2 = yt_service.control_video_playback('toggle_pause_play') # Should play
                print(f"Toggle 2 Result: {toggle_result_2}")

                # print("\n--- Testing Fullscreen ---")
                # yt_service.control_video_playback('fullscreen')
                # time.sleep(5)
                # print("\n--- Testing Exit Fullscreen (ESC) ---")
                # yt_service.control_video_playback('exit_fullscreen')
                # time.sleep(2)


            print("\n--- Testing Go Back ---")
            back_result = yt_service.go_back_in_browser_history()
            print(f"Go Back Result: {back_result}")
            time.sleep(3)


        # Test selecting a channel after a search
        # print("\n--- Testing Selecting Channel (after new search) ---")
        # yt_service.search_youtube("GoogleDevelopers") # Search for a channel
        # time.sleep(2)
        # channel_select_result = yt_service.select_channel_from_results()
        # print(f"Channel Select Result: {channel_select_result}")
        # time.sleep(3)


    except Exception as e:
        print(f"\nAn error occurred in YouTubeService example: {e}")
        traceback.print_exc()
    finally:
        if yt_service:
            print("\n--- Quitting WebDriver ---")
            yt_service.quit_driver()