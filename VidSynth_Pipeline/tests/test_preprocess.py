"""
Tests for the preprocess service.
"""
import os
import sys

# ---------------------------------------------------------------------------
# Path and environment setup (must come before importing service code)
# ---------------------------------------------------------------------------

# Set fake API key before config.py is imported (it raises ValueError if missing)
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

def test_preprocess_returns_comments(mock_youtube_client, client):
    """POST /preprocess with valid video_id should return comments."""
    mock_youtube_client.get_video_data.return_value = {
        "comments": "Great video!\nVery informative."
    }
    
    response = client.post("/preprocess", json={"video_id": "abc123"})
    
    assert response.status_code == 200
    data = response.json()
    assert data["video_id"] == "abc123"
    assert data["comments"] == "Great video!\nVery informative."


def test_preprocess_empty_comments(mock_youtube_client, client):
    """POST /preprocess when no comments exist should return empty string."""
    mock_youtube_client.get_video_data.return_value = {
        "comments": ""
    }
    
    response = client.post("/preprocess", json={"video_id": "xyz789"})
    
    assert response.status_code == 200
    data = response.json()
    assert data["video_id"] == "xyz789"
    assert data["comments"] == ""


def test_preprocess_calls_youtube_client_with_video_id(mock_youtube_client, client):
    """Verify youtube_client.get_video_data is called with the correct video_id."""
    mock_youtube_client.get_video_data.return_value = {"comments": ""}
    
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
# Tests for YouTubeClient class (unit tests with mocked Google API)
# ---------------------------------------------------------------------------

class TestYouTubeClient:
    """Unit tests for YouTubeClient methods."""
    
    @patch("youtube_client.build")
    @patch("youtube_client.config")
    def test_get_comments_parses_response(self, mock_config, mock_build):
        """_get_comments should extract textDisplay from API response."""
        mock_config.YOUTUBE_API_KEY = "fake_key"
        
        # Set up the mock API response structure
        mock_api = MagicMock()
        mock_build.return_value = mock_api
        
        mock_api.commentThreads.return_value.list.return_value.execute.return_value = {
            "items": [
                {"snippet": {"topLevelComment": {"snippet": {"textDisplay": "Comment 1"}}}},
                {"snippet": {"topLevelComment": {"snippet": {"textDisplay": "Comment 2"}}}},
            ]
        }
        
        from youtube_client import YouTubeClient
        client = YouTubeClient()
        result = client._get_comments("test_video")
        
        assert result == "Comment 1\nComment 2"
    
    @patch("youtube_client.build")
    @patch("youtube_client.config")
    def test_get_comments_handles_empty_response(self, mock_config, mock_build):
        """_get_comments should return empty string when no comments exist."""
        mock_config.YOUTUBE_API_KEY = "fake_key"
        
        mock_api = MagicMock()
        mock_build.return_value = mock_api
        mock_api.commentThreads.return_value.list.return_value.execute.return_value = {
            "items": []
        }
        
        from youtube_client import YouTubeClient
        client = YouTubeClient()
        result = client._get_comments("test_video")
        
        assert result == ""
    
    @patch("youtube_client.build")
    @patch("youtube_client.config")
    def test_get_comments_handles_api_exception(self, mock_config, mock_build):
        """_get_comments should return empty string and not raise on API error."""
        mock_config.YOUTUBE_API_KEY = "fake_key"
        
        mock_api = MagicMock()
        mock_build.return_value = mock_api
        mock_api.commentThreads.return_value.list.return_value.execute.side_effect = Exception("API Error")
        
        from youtube_client import YouTubeClient
        client = YouTubeClient()
        result = client._get_comments("test_video")
        
        assert result == ""  # Should gracefully return empty, not raise
