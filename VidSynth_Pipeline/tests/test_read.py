"""
Tests for the read service.
"""
import os
import sys

# ---------------------------------------------------------------------------
# Path setup (must come before importing service code)
# ---------------------------------------------------------------------------

# Add read service directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "read_service"))

import pytest
from fastapi.testclient import TestClient
from main import app, extract_video_id


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


# ---------------------------------------------------------------------------
# Tests for root endpoint
# ---------------------------------------------------------------------------

def test_root_returns_200(client):
    """GET / should return 200 with service status message."""
    response = client.get("/")
    
    assert response.status_code == 200
    assert response.json() == {"message": "VidSynth Read Service Running"}


# ---------------------------------------------------------------------------
# Unit tests for extract_video_id function
# ---------------------------------------------------------------------------

class TestExtractVideoId:
    """Unit tests for the extract_video_id helper function."""
    
    def test_youtu_be_short_link(self):
        """Should extract ID from youtu.be short links."""
        url = "https://youtu.be/dQw4w9WgXcQ"
        assert extract_video_id(url) == "dQw4w9WgXcQ"
    
    def test_youtube_watch_url(self):
        """Should extract ID from standard youtube.com/watch URLs."""
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        assert extract_video_id(url) == "dQw4w9WgXcQ"
    
    def test_youtube_watch_url_no_www(self):
        """Should extract ID from youtube.com URLs without www."""
        url = "https://youtube.com/watch?v=dQw4w9WgXcQ"
        assert extract_video_id(url) == "dQw4w9WgXcQ"
    
    def test_youtube_watch_url_with_extra_params(self):
        """Should extract ID even with additional query parameters."""
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=120"
        assert extract_video_id(url) == "dQw4w9WgXcQ"
    
    def test_youtube_embed_url(self):
        """Should extract ID from /embed/ URLs."""
        url = "https://www.youtube.com/embed/dQw4w9WgXcQ"
        assert extract_video_id(url) == "dQw4w9WgXcQ"
    
    def test_youtube_v_url(self):
        """Should extract ID from /v/ URLs."""
        url = "https://www.youtube.com/v/dQw4w9WgXcQ"
        assert extract_video_id(url) == "dQw4w9WgXcQ"
    
    def test_invalid_url_returns_none(self):
        """Should return None for non-YouTube URLs."""
        url = "https://vimeo.com/123456789"
        assert extract_video_id(url) is None
    
    def test_malformed_url_returns_none(self):
        """Should return None for malformed URLs."""
        url = "not-a-valid-url"
        assert extract_video_id(url) is None
    
    def test_youtube_url_missing_video_id(self):
        """Should return None when video ID is missing from watch URL."""
        url = "https://www.youtube.com/watch"
        assert extract_video_id(url) is None


# ---------------------------------------------------------------------------
# Tests for /read endpoint - success cases
# ---------------------------------------------------------------------------

def test_read_extracts_video_id_from_youtu_be(client):
    """POST /read with youtu.be link should return extracted video_id."""
    response = client.post("/read", json={"video_link": "https://youtu.be/abc123XYZ"})
    
    assert response.status_code == 200
    data = response.json()
    assert data["video_id"] == "abc123XYZ"
    assert data["original_link"] == "https://youtu.be/abc123XYZ"


def test_read_extracts_video_id_from_watch_url(client):
    """POST /read with youtube.com/watch link should return extracted video_id."""
    response = client.post("/read", json={"video_link": "https://www.youtube.com/watch?v=abc123XYZ"})
    
    assert response.status_code == 200
    data = response.json()
    assert data["video_id"] == "abc123XYZ"
    assert data["original_link"] == "https://www.youtube.com/watch?v=abc123XYZ"


def test_read_preserves_original_link(client):
    """POST /read should return the original link unchanged."""
    original = "https://youtu.be/testVideo123"
    response = client.post("/read", json={"video_link": original})
    
    assert response.status_code == 200
    assert response.json()["original_link"] == original


# ---------------------------------------------------------------------------
# Tests for /read endpoint - error cases
# ---------------------------------------------------------------------------

def test_read_invalid_url_returns_400(client):
    """POST /read with invalid YouTube URL should return 400."""
    response = client.post("/read", json={"video_link": "https://vimeo.com/123456"})
    
    assert response.status_code == 400
    assert "Invalid YouTube video link" in response.json()["detail"]


def test_read_missing_video_link_returns_422(client):
    """POST /read without video_link should return 422 validation error."""
    response = client.post("/read", json={})
    
    assert response.status_code == 422


def test_read_empty_string_returns_400(client):
    """POST /read with empty string should return 400."""
    response = client.post("/read", json={"video_link": ""})
    
    assert response.status_code == 400
