
import pytest
from unittest.mock import patch, MagicMock
from backend.app.services.spotify_service import SpotifyService


class DummyConfig:
    def get_spotify_credentials(self):
        return {
            "client_id": "test",
            "client_secret": "test",
            "redirect_uri": "http://localhost:8888/callback"
        }

@patch("backend.app.services.spotify_service.SpotifyOAuth")
@patch("backend.app.services.spotify_service.spotipy.Spotify")
def test_play_music_success(mock_spotify, mock_oauth):
    mock_client = MagicMock()
    mock_spotify.return_value = mock_client
    mock_client.search.return_value = {
        "tracks": {
            "items": [{
                "uri": "spotify:track:123",
                "name": "Test Song",
                "artists": [{"name": "Test Artist"}]
            }]
        }
    }
    service = SpotifyService(DummyConfig())
    result = service.play_music("Test Song")
    assert result["status"] == "success"

@patch("backend.app.services.spotify_service.SpotifyOAuth")
@patch("backend.app.services.spotify_service.spotipy.Spotify")
def test_play_music_not_found(mock_spotify, mock_oauth):
    mock_client = MagicMock()
    mock_spotify.return_value = mock_client
    mock_client.search.return_value = {
        "tracks": {"items": []}
    }
    service = SpotifyService(DummyConfig())
    result = service.play_music("Unknown Song")
    assert result["status"] == "error"
    assert "not found" in result["message"]

@patch("backend.app.services.spotify_service.SpotifyOAuth")
@patch("backend.app.services.spotify_service.spotipy.Spotify")
def test_pause_playback(mock_spotify, mock_oauth):
    mock_client = MagicMock()
    mock_spotify.return_value = mock_client
    service = SpotifyService(DummyConfig())
    result = service.pause_playback()
    assert result["status"] == "success"

@patch("backend.app.services.spotify_service.spotipy.Spotify")
def test_list_tracks_in_playlist(mock_spotify):
    mock_client = MagicMock()
    mock_spotify.return_value = mock_client
    mock_client.playlist.return_value = {"name": "My Playlist"}
    mock_client.playlist_items.return_value = {
        "items": [
            {
                "track": {
                    "name": "Song A",
                    "artists": [{"name": "Artist 1"}],
                    "uri": "uri-a"
                }
            },
            {
                "track": {
                    "name": "Song B",
                    "artists": [{"name": "Artist 2"}],
                    "uri": "uri-b"
                }
            }
        ]
    }

    mock_playlists = [{"id": "mock123", "name": "My Playlist"}]

    service = SpotifyService(DummyConfig())
    service.sp = mock_client
    result = service.list_tracks_in_playlist(1, playlists=mock_playlists)

    assert result["status"] == "success"
    assert len(result["tracks"]) == 2
    assert result["tracks"][0]["name"] == "Song A"

@patch("backend.app.services.spotify_service.spotipy.Spotify")
def test_add_track_to_playlist_success(mock_spotify):
    mock_client = MagicMock()
    mock_spotify.return_value = mock_client
    mock_client.search.return_value = {
        "tracks": {"items": [{"uri": "spotify:track:abc", "name": "Test Track"}]}
    }
    mock_client.playlist_add_items.return_value = None
    mock_client.playlist.return_value = {"name": "My Playlist"}

    mock_playlists = [{"id": "mock123", "name": "My Playlist"}]

    service = SpotifyService(DummyConfig())
    service.sp = mock_client
    result = service.add_track_to_playlist("Test Track", 1, playlists=mock_playlists)

    assert result["status"] == "success"
    assert "added" in result["message"]

@patch("backend.app.services.spotify_service.spotipy.Spotify")
def test_get_playlist_id_by_index(mock_spotify):
    service = SpotifyService(DummyConfig())
    mock_playlists = [
        {"id": "abc123", "name": "Chill Vibes"},
        {"id": "def456", "name": "Top Hits"},
    ]
    result = service.get_playlist_id_by_name_or_index(2, playlists=mock_playlists)
    assert result == "def456"

@patch("backend.app.services.spotify_service.spotipy.Spotify")
def test_get_playlist_id_by_name(mock_spotify):
    service = SpotifyService(DummyConfig())
    mock_playlists = [
        {"id": "abc123", "name": "Chill Vibes"},
        {"id": "def456", "name": "Top Hits"},
    ]
    result = service.get_playlist_id_by_name_or_index("Chill Vibes", playlists=mock_playlists)
    assert result == "abc123"
