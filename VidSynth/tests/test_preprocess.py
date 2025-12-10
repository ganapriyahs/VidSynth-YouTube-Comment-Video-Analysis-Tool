"""
Tests for the preprocess service.
"""
import os
import sys

# ---------------------------------------------------------------------------
# Path and environment setup (must come before importing service code)
# ---------------------------------------------------------------------------

# Set fake API key before youtube_client.py is imported
os.environ["YOUTUBE_API_KEY"] = "fake_key_for_testing"

# Add preprocess service directory to Python path
# This allows `from main import app` to find preprocess_service/main.py
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "preprocess_service"))

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    from main import app
    return TestClient(app)


@pytest.fixture
def mock_youtube_client():
    """Fixture that patches youtube_client in main.py and returns the mock."""
    with patch("main.youtube_client") as mock:
        yield mock


# ---------------------------------------------------------------------------
# Tests for root endpoint
# ---------------------------------------------------------------------------

def test_root_returns_200(client):
    """GET / should return 200 with service status message."""
    response = client.get("/")
    
    assert response.status_code == 200
    assert response.json() == {"message": "VidSynth Preprocess Service Running"}


# ---------------------------------------------------------------------------
# Tests for /preprocess endpoint - success cases
# ---------------------------------------------------------------------------

def test_preprocess_returns_all_fields(mock_youtube_client, client):
    """POST /preprocess with valid video_id should return transcript, comments, and title."""
    mock_youtube_client.get_video_data.return_value = {
        "transcript": "This is the video transcript.",
        "comments": "Great video!\nVery informative.",
        "video_title": "Test Video Title"
    }
    
    response = client.post("/preprocess", json={"video_id": "abc123"})
    
    assert response.status_code == 200
    data = response.json()
    assert data["video_id"] == "abc123"
    assert data["transcript"] == "This is the video transcript."
    assert data["comments"] == "Great video!\nVery informative."
    assert data["video_title"] == "Test Video Title"


def test_preprocess_empty_transcript_and_comments(mock_youtube_client, client):
    """POST /preprocess when no data exists should return empty strings."""
    mock_youtube_client.get_video_data.return_value = {
        "transcript": "",
        "comments": "",
        "video_title": "Video With No Data"
    }
    
    response = client.post("/preprocess", json={"video_id": "xyz789"})
    
    assert response.status_code == 200
    data = response.json()
    assert data["video_id"] == "xyz789"
    assert data["transcript"] == ""
    assert data["comments"] == ""
    assert data["video_title"] == "Video With No Data"


def test_preprocess_missing_video_title_uses_default(mock_youtube_client, client):
    """POST /preprocess should use 'Unknown Title' if video_title not in response."""
    mock_youtube_client.get_video_data.return_value = {
        "transcript": "Some transcript",
        "comments": "Some comments"
        # video_title intentionally missing
    }
    
    response = client.post("/preprocess", json={"video_id": "abc123"})
    
    assert response.status_code == 200
    data = response.json()
    assert data["video_title"] == "Unknown Title"


def test_preprocess_calls_youtube_client_with_video_id(mock_youtube_client, client):
    """Verify youtube_client.get_video_data is called with the correct video_id."""
    mock_youtube_client.get_video_data.return_value = {
        "transcript": "",
        "comments": "",
        "video_title": "Title"
    }
    
    client.post("/preprocess", json={"video_id": "test_id_123"})
    
    mock_youtube_client.get_video_data.assert_called_once_with("test_id_123")


# ---------------------------------------------------------------------------
# Tests for /preprocess endpoint - validation errors
# ---------------------------------------------------------------------------

def test_preprocess_missing_video_id_returns_422(client):
    """POST /preprocess without video_id should return 422 validation error."""
    response = client.post("/preprocess", json={})
    
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Tests for /preprocess endpoint - error handling
# ---------------------------------------------------------------------------

def test_preprocess_youtube_error_returns_500(mock_youtube_client, client):
    """POST /preprocess should return 500 when youtube_client raises exception."""
    mock_youtube_client.get_video_data.side_effect = Exception("API quota exceeded")
    
    response = client.post("/preprocess", json={"video_id": "abc123"})
    
    assert response.status_code == 500
    assert "Internal server error" in response.json()["detail"]


# ---------------------------------------------------------------------------
# Tests for YouTubeClient class (unit tests with mocked external calls)
# ---------------------------------------------------------------------------

class TestYouTubeClientComments:
    """Unit tests for YouTubeClient._get_comments method."""
    
    @patch("youtube_client.build")
    def test_get_comments_parses_response(self, mock_build):
        """_get_comments should extract textDisplay from API response."""
        mock_api = MagicMock()
        mock_build.return_value = mock_api
        
        mock_api.commentThreads.return_value.list.return_value.execute.return_value = {
            "items": [
                {"snippet": {"topLevelComment": {"snippet": {"textDisplay": "Comment 1"}}}},
                {"snippet": {"topLevelComment": {"snippet": {"textDisplay": "Comment 2"}}}},
            ]
        }
        
        from youtube_client import YouTubeClient
        yt_client = YouTubeClient()
        result = yt_client._get_comments("test_video")
        
        assert result == "Comment 1\nComment 2"
    
    @patch("youtube_client.build")
    def test_get_comments_handles_empty_response(self, mock_build):
        """_get_comments should return empty string when no comments exist."""
        mock_api = MagicMock()
        mock_build.return_value = mock_api
        mock_api.commentThreads.return_value.list.return_value.execute.return_value = {
            "items": []
        }
        
        from youtube_client import YouTubeClient
        yt_client = YouTubeClient()
        result = yt_client._get_comments("test_video")
        
        assert result == ""
    
    @patch("youtube_client.build")
    def test_get_comments_handles_api_exception(self, mock_build):
        """_get_comments should return empty string on API error."""
        mock_api = MagicMock()
        mock_build.return_value = mock_api
        mock_api.commentThreads.return_value.list.return_value.execute.side_effect = Exception("API Error")
        
        from youtube_client import YouTubeClient
        yt_client = YouTubeClient()
        result = yt_client._get_comments("test_video")
        
        assert result == ""


class TestYouTubeClientVideoTitle:
    """Unit tests for YouTubeClient._get_video_title method."""
    
    @patch("youtube_client.build")
    def test_get_video_title_returns_title(self, mock_build):
        """_get_video_title should extract title from API response."""
        mock_api = MagicMock()
        mock_build.return_value = mock_api
        
        mock_api.videos.return_value.list.return_value.execute.return_value = {
            "items": [{"snippet": {"title": "My Awesome Video"}}]
        }
        
        from youtube_client import YouTubeClient
        yt_client = YouTubeClient()
        result = yt_client._get_video_title("test_video")
        
        assert result == "My Awesome Video"
    
    @patch("youtube_client.build")
    def test_get_video_title_handles_no_items(self, mock_build):
        """_get_video_title should return 'Unknown' when video not found."""
        mock_api = MagicMock()
        mock_build.return_value = mock_api
        mock_api.videos.return_value.list.return_value.execute.return_value = {
            "items": []
        }
        
        from youtube_client import YouTubeClient
        yt_client = YouTubeClient()
        result = yt_client._get_video_title("nonexistent_video")
        
        assert result == "Unknown"
    
    @patch("youtube_client.build")
    def test_get_video_title_handles_api_exception(self, mock_build):
        """_get_video_title should return 'Unknown' on API error."""
        mock_api = MagicMock()
        mock_build.return_value = mock_api
        mock_api.videos.return_value.list.return_value.execute.side_effect = Exception("API Error")
        
        from youtube_client import YouTubeClient
        yt_client = YouTubeClient()
        result = yt_client._get_video_title("test_video")
        
        assert result == "Unknown"


class TestYouTubeClientTranscript:
    """Unit tests for YouTubeClient._get_transcript method."""
    
    @patch("youtube_client.yt_dlp.YoutubeDL")
    @patch("youtube_client.build")
    def test_get_transcript_with_manual_captions(self, mock_build, mock_ydl_class):
        """_get_transcript should return transcript when manual captions exist."""
        mock_build.return_value = MagicMock()
        
        # Mock yt_dlp context manager
        mock_ydl_instance = MagicMock()
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl_instance
        mock_ydl_instance.extract_info.return_value = {
            "subtitles": {
                "en": [{"url": "http://example.com/subs.vtt", "ext": "vtt"}]
            }
        }
        
        # Mock the _download_subs_text method to avoid HTTP call
        with patch.object(
            __import__("youtube_client", fromlist=["YouTubeClient"]).YouTubeClient,
            "_download_subs_text",
            return_value="This is the transcript text."
        ):
            from youtube_client import YouTubeClient
            yt_client = YouTubeClient()
            result = yt_client._get_transcript("test_video")
        
        assert result == "This is the transcript text."
    
    @patch("youtube_client.yt_dlp.YoutubeDL")
    @patch("youtube_client.build")
    def test_get_transcript_with_auto_captions(self, mock_build, mock_ydl_class):
        """_get_transcript should fall back to auto-generated captions."""
        mock_build.return_value = MagicMock()
        
        mock_ydl_instance = MagicMock()
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl_instance
        mock_ydl_instance.extract_info.return_value = {
            "automatic_captions": {
                "en": [{"url": "http://example.com/auto.vtt", "ext": "vtt"}]
            }
        }
        
        with patch.object(
            __import__("youtube_client", fromlist=["YouTubeClient"]).YouTubeClient,
            "_download_subs_text",
            return_value="Auto-generated transcript."
        ):
            from youtube_client import YouTubeClient
            yt_client = YouTubeClient()
            result = yt_client._get_transcript("test_video")
        
        assert result == "Auto-generated transcript."
    
    @patch("youtube_client.yt_dlp.YoutubeDL")
    @patch("youtube_client.build")
    def test_get_transcript_no_captions_returns_empty(self, mock_build, mock_ydl_class):
        """_get_transcript should return empty string when no captions exist."""
        mock_build.return_value = MagicMock()
        
        mock_ydl_instance = MagicMock()
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl_instance
        mock_ydl_instance.extract_info.return_value = {}  # No subtitles
        
        from youtube_client import YouTubeClient
        yt_client = YouTubeClient()
        result = yt_client._get_transcript("test_video")
        
        assert result == ""


class TestYouTubeClientGetVideoData:
    """Unit tests for YouTubeClient.get_video_data method."""
    
    @patch("youtube_client.build")
    def test_get_video_data_returns_all_fields(self, mock_build):
        """get_video_data should return dict with transcript, comments, and video_title."""
        mock_build.return_value = MagicMock()
        
        from youtube_client import YouTubeClient
        yt_client = YouTubeClient()
        
        # Mock the individual methods
        with patch.object(yt_client, "_get_transcript", return_value="transcript text"):
            with patch.object(yt_client, "_get_comments", return_value="comments text"):
                with patch.object(yt_client, "_get_video_title", return_value="Video Title"):
                    result = yt_client.get_video_data("test_video")
        
        assert result == {
            "transcript": "transcript text",
            "comments": "comments text",
            "video_title": "Video Title"
        }
