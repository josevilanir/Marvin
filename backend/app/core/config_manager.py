# backend/app/core/config_manager.py
import os
from dotenv import load_dotenv

class ConfigManager:
    """
    Manages the application's configuration.
    Loads settings from environment variables or a .env file.
    """

    def __init__(self, env_file_path: str = None):
        """
        Initializes the ConfigManager.

        Args:
            env_file_path (str, optional): Path to the .env file.
                                           If None, attempts to load from '.env' in the project root
                                           or relies solely on environment variables.
        """
        if env_file_path:
            load_dotenv(dotenv_path=env_file_path)
        else:
            # Try to find .env in the root of the backend or project
            # This path might need adjustment based on your project structure
            # For a structure like marvin_professional/backend/.env
            backend_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            project_root_env = os.path.join(os.path.dirname(backend_root), '.env') # marvin_professional/.env
            backend_env = os.path.join(backend_root, '.env') # marvin_professional/backend/.env

            if os.path.exists(project_root_env):
                load_dotenv(dotenv_path=project_root_env)
            elif os.path.exists(backend_env):
                load_dotenv(dotenv_path=backend_env)
            else:
                # If no .env file is found, it will rely on system environment variables
                # You might want to log a warning here if a .env file was expected
                print("Warning: .env file not found. Relying on system environment variables.")
                load_dotenv()


        # Spotify Configurations
        self.spotify_client_id: str = os.getenv("SPOTIPY_CLIENT_ID")
        self.spotify_client_secret: str = os.getenv("SPOTIPY_CLIENT_SECRET")
        self.spotify_redirect_uri: str = os.getenv("SPOTIPY_REDIRECT_URI")

        self._validate_spotify_config()

    def _validate_spotify_config(self):
        """
        Validates that essential Spotify configurations are present.
        Raises ValueError if any required config is missing.
        """
        if not all([self.spotify_client_id, self.spotify_client_secret, self.spotify_redirect_uri]):
            missing_configs = []
            if not self.spotify_client_id:
                missing_configs.append("SPOTIPY_CLIENT_ID")
            if not self.spotify_client_secret:
                missing_configs.append("SPOTIPY_CLIENT_SECRET")
            if not self.spotify_redirect_uri:
                missing_configs.append("SPOTIPY_REDIRECT_URI")
            raise ValueError(f"Missing Spotify configuration(s): {', '.join(missing_configs)}. "
                             "Please set them in your .env file or environment variables.")

    def get_spotify_credentials(self) -> dict:
        """
        Returns a dictionary with Spotify API credentials.
        """
        return {
            "client_id": self.spotify_client_id,
            "client_secret": self.spotify_client_secret,
            "redirect_uri": self.spotify_redirect_uri,
        }

# Global instance (optional, can be instantiated where needed)
# config = ConfigManager()

if __name__ == '__main__':
    # Example usage:
    # Create a .env file in the root of your project (e.g., marvin_professional/.env) with:
    # SPOTIPY_CLIENT_ID="your_id"
    # SPOTIPY_CLIENT_SECRET="your_secret"
    # SPOTIPY_REDIRECT_URI="your_redirect_uri"

    try:
        # If running this file directly for testing, it might look for .env
        # relative to this file or the backend root.
        # Adjust the path if necessary for direct execution.
        # For example, if .env is in marvin_professional/
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        env_path = os.path.join(os.path.dirname(project_root), '.env')

        if not os.path.exists(env_path):
             # Try marvin_professional/backend/.env
             env_path = os.path.join(project_root, '.env')


        if os.path.exists(env_path):
            print(f"Attempting to load .env from: {env_path}")
            cfg_manager = ConfigManager(env_file_path=env_path)
            print("ConfigManager initialized successfully.")
            print(f"Spotify Client ID: {cfg_manager.spotify_client_id}")
            creds = cfg_manager.get_spotify_credentials()
            print(f"Spotify Credentials from getter: {creds}")
        else:
            print(f"Test .env file not found at {env_path}. Create it for testing.")
            print("Attempting to load from environment variables only.")
            cfg_manager = ConfigManager() # Relies on env vars
            print(f"Spotify Client ID from env: {cfg_manager.spotify_client_id}")


    except ValueError as e:
        print(f"Configuration Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")