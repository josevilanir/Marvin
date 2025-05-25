# backend/app/services/spotify_service.py
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from spotipy.exceptions import SpotifyException
from backend.app.core.config_manager import ConfigManager
from backend.app.utils.numeros_por_extenso_para_numero import numero_por_extenso_para_numero
import os

class SpotifyService:
    """
    Service class for interacting with the Spotify API.
    """

    def __init__(self, config_manager: ConfigManager):
        """
        Initializes the SpotifyService.

        Args:
            config_manager (ConfigManager): Instance of ConfigManager for accessing API keys.
        """
        self.config = config_manager
        spotify_creds = self.config.get_spotify_credentials()

        # Define a more comprehensive scope based on the project's needs
        # Original scopes: "user-read-playback-state,user-modify-playback-state"
        # Scopes from tocar_musica.py: "user-read-playback-state,user-modify-playback-state,playlist-modify-private,playlist-modify-public,playlist-read-private"
        self.scope = "user-read-playback-state,user-modify-playback-state,playlist-read-private,playlist-modify-public,playlist-modify-private,user-library-read,user-library-modify,user-top-read"

        try:
            self.sp = spotipy.Spotify(
                auth_manager=SpotifyOAuth(
                    client_id=spotify_creds["client_id"],
                    client_secret=spotify_creds["client_secret"],
                    redirect_uri=spotify_creds["redirect_uri"],
                    scope=self.scope
                )
            )
            # Try a simple call to verify authentication
            self.sp.me()
            print("SpotifyService: Successfully authenticated with Spotify.")
        except SpotifyException as e:
            print(f"SpotifyService: Error during Spotify authentication: {e}")
            # Handle specific auth errors if needed, e.g., redirect user to auth URL
            # For a desktop app, the auth flow might open a browser window.
            # spotipy handles this by printing a URL to the console.
            # Consider how to manage this in a desktop app context.
            raise  # Re-raise the exception if auth is critical for initialization
        except Exception as e:
            print(f"SpotifyService: An unexpected error occurred during Spotify client initialization: {e}")
            raise


    def list_available_devices(self) -> list:
        """
        Lists available Spotify devices.
        Based on a similar function in the original spotify_utils.py.
        """
        try:
            devices = self.sp.devices()
            return devices['devices'] if devices and devices['devices'] else []
        except SpotifyException as e:
            print(f"Error listing Spotify devices: {e}")
            return []
        except AttributeError: # If self.sp is None due to failed init
            print("Error listing Spotify devices: Spotify client not initialized.")
            return []


    def transfer_playback(self, device_id: str, force_play: bool = True) -> bool:
        """
        Transfers playback to a specific device.
        Args:
            device_id (str): The ID of the device to transfer playback to.
            force_play (bool): Whether to force playback after transfer.

        Returns:
            bool: True if successful, False otherwise.
        """
        if not device_id:
            print("Error transferring playback: Device ID is required.")
            return False
        try:
            self.sp.transfer_playback(device_id=device_id, force_play=force_play)
            print(f"Playback transferred to device: {device_id}")
            return True
        except SpotifyException as e:
            print(f"Error transferring Spotify playback: {e}")
            return False
        except AttributeError:
            print("Error transferring playback: Spotify client not initialized.")
            return False

    def play_music(self, track_name: str, device_id: str = None) -> dict:
        """
        Searches for a track and starts playback.

        Args:
            track_name (str): The name of the track to play.
            device_id (str, optional): The ID of the device to play on. Defaults to None (active device).

        Returns:
            dict: A dictionary containing status and a message.
                  Example: {"status": "success", "message": "Playing 'Song Title' by Artist"}
                           {"status": "error", "message": "Track not found."}
        """
        if not track_name:
            return {"status": "error", "message": "Track name is required."}
        try:
            results = self.sp.search(q=track_name, type='track', limit=1)
            if results['tracks']['items']:
                track = results['tracks']['items'][0]
                track_uri = track['uri']
                track_info = f"'{track['name']}' by {track['artists'][0]['name']}"
                
                playback_args = {'uris': [track_uri]}
                if device_id:
                    playback_args['device_id'] = device_id
                
                self.sp.start_playback(**playback_args)
                return {"status": "success", "message": f"Playing {track_info}"}
            else:
                return {"status": "error", "message": f"Track '{track_name}' not found."}
        except SpotifyException as e:
            return {"status": "error", "message": f"Spotify error: {e}"}
        except AttributeError:
            return {"status": "error", "message": "Spotify client not initialized."}


    def pause_playback(self, device_id: str = None) -> dict:
        """Pauses the current playback."""
        try:
            self.sp.pause_playback(device_id=device_id)
            return {"status": "success", "message": "Playback paused."}
        except SpotifyException as e:
            # Spotify API can return 404 if no active device or nothing playing
            if e.http_status == 404 and "Player command failed: No active device found" in str(e):
                 return {"status": "error", "message": "No active Spotify device found to pause."}
            if e.http_status == 404 and ("Restriction violated" in str(e) or "Player command failed: No track currently playing" in str(e)):
                 return {"status": "warn", "message": "Nothing is currently playing or device is restricted."}
            return {"status": "error", "message": f"Error pausing playback: {e}"}
        except AttributeError:
            return {"status": "error", "message": "Spotify client not initialized."}


    def resume_playback(self, device_id: str = None) -> dict:
        """Resumes the current playback."""
        try:
            self.sp.start_playback(device_id=device_id) # `start_playback` also resumes
            return {"status": "success", "message": "Playback resumed."}
        except SpotifyException as e:
            if e.http_status == 404 and "Player command failed: No active device found" in str(e):
                 return {"status": "error", "message": "No active Spotify device found to resume."}
            if e.http_status == 403 and "Player command failed: Restricted device" in str(e):
                 return {"status": "error", "message": "Cannot control this Spotify device (possibly a cast device or restricted)."}
            return {"status": "error", "message": f"Error resuming playback: {e}"}
        except AttributeError:
            return {"status": "error", "message": "Spotify client not initialized."}

    def next_track(self, device_id: str = None) -> dict:
        """Skips to the next track."""
        try:
            self.sp.next_track(device_id=device_id)
            return {"status": "success", "message": "Skipped to the next track."}
        except SpotifyException as e:
            return {"status": "error", "message": f"Error skipping to next track: {e}"}
        except AttributeError:
            return {"status": "error", "message": "Spotify client not initialized."}

    def previous_track(self, device_id: str = None) -> dict:
        """Skips to the previous track."""
        try:
            self.sp.previous_track(device_id=device_id)
            return {"status": "success", "message": "Skipped to the previous track."}
        except SpotifyException as e:
            return {"status": "error", "message": f"Error skipping to previous track: {e}"}
        except AttributeError:
            return {"status": "error", "message": "Spotify client not initialized."}

    def list_user_playlists(self) -> list:
        """
        Lists the current user's playlists.
        Returns a list of playlist objects, or an empty list on error.
        """
        try:
            playlists_response = self.sp.current_user_playlists(limit=50)
            return playlists_response['items'] if playlists_response else []
        except SpotifyException as e:
            print(f"Error listing user playlists: {e}")
            return []
        except AttributeError:
            print("Error listing playlists: Spotify client not initialized.")
            return []

    def get_playlist_id_by_name_or_index(self, playlist_identifier, playlists: list = None) -> str | None:
        """
        Finds a playlist ID by its name or 1-based index.

        Args:
            playlist_identifier (str | int): The name of the playlist or its 1-based index.
            playlists (list, optional): A pre-fetched list of playlist items. 
                                        If None, fetches current user playlists.

        Returns:
            str | None: The playlist ID if found, otherwise None.
        """
        if playlists is None:
            playlists = self.list_user_playlists()

        if not playlists:
            return None

        playlist_id_to_return = None
        
        # Try to convert to number if it's a spoken number
        numerical_choice = numero_por_extenso_para_numero(playlist_identifier)
        if numerical_choice is not None:
            playlist_identifier = numerical_choice # Use the converted number

        if isinstance(playlist_identifier, int):
            if 1 <= playlist_identifier <= len(playlists):
                playlist_id_to_return = playlists[playlist_identifier - 1]['id']
            else:
                print(f"Playlist index {playlist_identifier} is out of range (1-{len(playlists)}).")
        elif isinstance(playlist_identifier, str):
            # Search by name (case-insensitive)
            for pl in playlists:
                if playlist_identifier.lower() == pl['name'].lower():
                    playlist_id_to_return = pl['id']
                    break
            if not playlist_id_to_return:
                 print(f"Playlist with name '{playlist_identifier}' not found.")
        else:
            print(f"Invalid playlist identifier type: {type(playlist_identifier)}.")
            
        return playlist_id_to_return

    def play_playlist(self, playlist_identifier, mode: str = 'standard', device_id: str = None) -> dict:
        """
        Plays a specified playlist by name or 1-based index.

        Args:
            playlist_identifier (str | int): The name or 1-based index of the playlist.
            mode (str, optional): 'standard' or 'shuffle'. Defaults to 'standard'.
            device_id (str, optional): The ID of the device to play on.

        Returns:
            dict: Status and message.
        """
        playlist_id = self.get_playlist_id_by_name_or_index(playlist_identifier)

        if not playlist_id:
            message = f"Playlist '{playlist_identifier}' not found or identifier is invalid."
            if isinstance(playlist_identifier, int): # If it was an out-of-range index
                message = f"Playlist at index {playlist_identifier} not found."
            return {"status": "error", "message": message}

        playlist_uri = f"spotify:playlist:{playlist_id}"
        try:
            playback_args = {'context_uri': playlist_uri}
            if device_id:
                playback_args['device_id'] = device_id

            # Set shuffle mode
            shuffle_state = (mode.lower() == 'shuffle')
            self.sp.shuffle(shuffle_state, device_id=device_id) # Shuffle must be set before starting playback for it to take effect immediately on some clients
            
            self.sp.start_playback(**playback_args)
            
            # Get playlist name for feedback
            playlist_details = self.sp.playlist(playlist_id, fields="name")
            playlist_name = playlist_details.get("name", playlist_identifier)

            return {"status": "success", "message": f"Playing playlist '{playlist_name}' in {mode} mode."}
        except SpotifyException as e:
            return {"status": "error", "message": f"Error playing playlist: {e}"}
        except AttributeError:
            return {"status": "error", "message": "Spotify client not initialized."}

    def add_track_to_playlist(self, track_name: str, playlist_identifier) -> dict:
        """
        Adds a track to a specified playlist.

        Args:
            track_name (str): The name of the track to add.
            playlist_identifier (str | int): The name or 1-based index of the target playlist.

        Returns:
            dict: Status and message.
        """
        if not track_name:
            return {"status": "error", "message": "Track name is required to add to playlist."}

        # Find track URI
        try:
            results = self.sp.search(q=track_name, type='track', limit=1)
            if not results['tracks']['items']:
                return {"status": "error", "message": f"Track '{track_name}' not found."}
            track_uri = results['tracks']['items'][0]['uri']
            found_track_name = results['tracks']['items'][0]['name']
        except SpotifyException as e:
            return {"status": "error", "message": f"Error searching for track '{track_name}': {e}"}
        except AttributeError:
            return {"status": "error", "message": "Spotify client not initialized."}


        # Find playlist ID
        playlist_id = self.get_playlist_id_by_name_or_index(playlist_identifier)
        if not playlist_id:
            message = f"Playlist '{playlist_identifier}' not found or identifier is invalid."
            if isinstance(playlist_identifier, int):
                message = f"Playlist at index {playlist_identifier} not found."
            return {"status": "error", "message": message}

        # Get playlist name for feedback
        try:
            playlist_details = self.sp.playlist(playlist_id, fields="name")
            playlist_name = playlist_details.get("name", playlist_identifier)
        except SpotifyException:
            playlist_name = str(playlist_identifier) # Fallback

        # Add track to playlist
        try:
            self.sp.playlist_add_items(playlist_id, [track_uri])
            return {"status": "success", "message": f"Track '{found_track_name}' added to playlist '{playlist_name}'."}
        except SpotifyException as e:
            return {"status": "error", "message": f"Error adding track to playlist '{playlist_name}': {e}"}

    def list_tracks_in_playlist(self, playlist_identifier) -> dict:
        """
        Lists tracks in a specified playlist.

        Args:
            playlist_identifier (str | int): The name or 1-based index of the playlist.

        Returns:
            dict: Contains status, message, and optionally a list of tracks if successful.
                  Tracks are dictionaries with 'name' and 'artists'.
        """
        playlist_id = self.get_playlist_id_by_name_or_index(playlist_identifier)
        if not playlist_id:
            message = f"Playlist '{playlist_identifier}' not found or identifier is invalid."
            if isinstance(playlist_identifier, int):
                message = f"Playlist at index {playlist_identifier} not found."
            return {"status": "error", "message": message}
        
        try:
            playlist_name = self.sp.playlist(playlist_id, fields="name").get("name", str(playlist_identifier))
            results = self.sp.playlist_items(playlist_id, fields="items(track(name,artists(name),uri)),next")
            tracks_data = []
            for item in results['items']:
                if item and item['track']: # Ensure track is not None (e.g., local files not synced)
                    track = item['track']
                    artist_names = ', '.join([artist['name'] for artist in track.get('artists', [])])
                    tracks_data.append({"name": track.get('name', 'Unknown Track'), "artists": artist_names, "uri": track.get('uri')})
            
            if not tracks_data:
                return {"status": "success", "message": f"Playlist '{playlist_name}' is empty.", "tracks": []}
            
            return {"status": "success", 
                    "message": f"Tracks in playlist '{playlist_name}':", 
                    "tracks": tracks_data,
                    "playlist_name": playlist_name}
        except SpotifyException as e:
            return {"status": "error", "message": f"Error listing tracks from playlist: {e}"}
        except AttributeError:
            return {"status": "error", "message": "Spotify client not initialized."}


if __name__ == '__main__':
    # Example Usage (requires .env file to be set up correctly as described in config_manager.py)
    try:
        print("Attempting to initialize ConfigManager for SpotifyService example...")
        # This assumes .env is in marvin_professional/ or marvin_professional/backend/
        # Adjust if your execution context or .env location is different
        backend_root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # app folder
        config_env_path = os.path.join(os.path.dirname(os.path.dirname(backend_root_path)), '.env') # marvin_professional/.env
        if not os.path.exists(config_env_path):
            config_env_path = os.path.join(os.path.dirname(backend_root_path), '.env') # marvin_professional/backend/.env
        
        if os.path.exists(config_env_path):
             print(f"Loading .env from: {config_env_path}")
             cfg = ConfigManager(env_file_path=config_env_path)
        else:
            print(f"Test .env not found at expected paths, attempting to load from environment variables for testing.")
            cfg = ConfigManager()


        print("Initializing SpotifyService...")
        spotify_service = SpotifyService(cfg)
        print("SpotifyService initialized.")

        print("\n--- Testing Device Listing ---")
        devices = spotify_service.list_available_devices()
        if devices:
            print("Available devices:")
            for i, device in enumerate(devices):
                print(f"  {i+1}. {device['name']} (ID: {device['id']}, Type: {device['type']}, Active: {device.get('is_active', False)})")
            # Example: transfer playback to the first device if available
            # if devices:
            #     spotify_service.transfer_playback(devices[0]['id'])
        else:
            print("No devices found or error listing devices.")

        print("\n--- Testing Playlist Listing ---")
        playlists = spotify_service.list_user_playlists()
        if playlists:
            print("User playlists:")
            for i, pl in enumerate(playlists):
                print(f"  {i+1}. {pl['name']} (ID: {pl['id']})")
        else:
            print("No playlists found or error listing them.")
        
        # print("\n--- Testing Playing a Song ---")
        # play_result = spotify_service.play_music("Bohemian Rhapsody")
        # print(f"Play song result: {play_result}")

        # time.sleep(5) # Let it play for a bit

        # print("\n--- Testing Pausing Playback ---")
        # pause_result = spotify_service.pause_playback()
        # print(f"Pause result: {pause_result}")

        # time.sleep(2)

        # print("\n--- Testing Resuming Playback ---")
        # resume_result = spotify_service.resume_playback()
        # print(f"Resume result: {resume_result}")

        # Example: Play a specific playlist (replace 'Your Playlist Name' or use an index)
        # if playlists:
        #     print("\n--- Testing Playing a Playlist by Name ---")
        #     # playlist_to_play = playlists[0]['name'] # Play the first playlist by name
        #     playlist_to_play = 1 # Play the first playlist by index
        #     play_playlist_result = spotify_service.play_playlist(playlist_to_play, mode='shuffle')
        #     print(f"Play playlist result: {play_playlist_result}")

        # Example: List tracks from a specific playlist
        # if playlists:
        #     print("\n--- Testing Listing Tracks from Playlist ---")
        #     tracks_result = spotify_service.list_tracks_in_playlist(1) # List tracks from first playlist
        #     print(f"List tracks result: {tracks_result['message']}")
        #     if tracks_result['status'] == 'success' and 'tracks' in tracks_result:
        #         for track in tracks_result['tracks'][:5]: # Print first 5 tracks
        #             print(f"  - {track['name']} by {track['artists']}")


    except ValueError as ve:
        print(f"ValueError during example: {ve}")
    except SpotifyException as se:
        print(f"SpotifyException during example: {se}")
        if se.http_status == 401: # Unauthorized
             print("Hint: Spotify authentication failed. Check your credentials and ensure you've authenticated.")
             print("If running for the first time, Spotipy might print a URL to visit for authentication.")
    except Exception as ex:
        print(f"An unexpected error occurred in example: {ex}")
        import traceback
        traceback.print_exc()