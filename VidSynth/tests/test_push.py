"""
Tests for the push service.
"""
import os
import sys
import json

# ---------------------------------------------------------------------------
# Path setup (must come before importing service code)
# ---------------------------------------------------------------------------

# Add push service directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "push_service"))

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from main import app, BUCKET_NAME


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def valid_push_input():
    """Valid input from validate service."""
    return {
        "video_id": "abc123",
        "video_summary": "This is the video summary.",
        "comment_summary": "This is the comment summary.",
        "is_valid": True,
        "issues": [],
        "video_title": "Test Video Title",
        "bias_check": {
            "similarity_score": 0.75,
            "is_biased": False,
            "threshold": 0.30,
            "summary_preview": "This is the video...",
            "video_title": "Test Video Title"
        }
    }


@pytest.fixture
def mock_gcs():
    """Mock Google Cloud Storage client and its chain of calls."""
    with patch("main.storage.Client") as mock_client_class:
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        mock_bucket = MagicMock()
        mock_client.bucket.return_value = mock_bucket
        
        mock_blob = MagicMock()
        mock_bucket.blob.return_value = mock_blob
        
        yield {
            "client_class": mock_client_class,
            "client": mock_client,
            "bucket": mock_bucket,
            "blob": mock_blob
        }


# ---------------------------------------------------------------------------
# Tests for root endpoint
# ---------------------------------------------------------------------------

def test_root_returns_200(client):
    """GET / should return 200 with service status message."""
    response = client.get("/")
    
    assert response.status_code == 200
    assert response.json() == {"message": "VidSynth Push Service Running (FastAPI)"}


def test_health_check_returns_200(client):
    """GET /health should return healthy status."""
    response = client.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "push_service"


# ---------------------------------------------------------------------------
# Tests for /push endpoint - success cases
# ---------------------------------------------------------------------------

def test_push_returns_success(mock_gcs, client, valid_push_input):
    """POST /push with valid input should return status='pushed'."""
    response = client.post("/push", json=valid_push_input)
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "pushed"
    assert data["video_id"] == "abc123"


def test_push_uploads_to_correct_bucket(mock_gcs, client, valid_push_input):
    """POST /push should upload to the configured bucket."""
    client.post("/push", json=valid_push_input)
    
    # Uses BUCKET_NAME from main.py - test stays in sync if it changes
    mock_gcs["client"].bucket.assert_called_once_with(BUCKET_NAME)


def test_push_creates_blob_with_video_id_filename(mock_gcs, client, valid_push_input):
    """POST /push should create blob named {video_id}.json."""
    client.post("/push", json=valid_push_input)
    
    mock_gcs["bucket"].blob.assert_called_once_with("abc123.json")


def test_push_uploads_correct_json_structure(mock_gcs, client, valid_push_input):
    """POST /push should upload JSON with required structure for extension."""
    client.post("/push", json=valid_push_input)
    
    # Get the data that was uploaded
    call_args = mock_gcs["blob"].upload_from_string.call_args
    uploaded_data = json.loads(call_args.kwargs["data"])
    
    assert uploaded_data["status"] == "ready"
    assert uploaded_data["video_id"] == "abc123"
    assert uploaded_data["data"]["video_summary"] == "This is the video summary."
    assert uploaded_data["data"]["comment_summary"] == "This is the comment summary."


def test_push_uploads_with_json_content_type(mock_gcs, client, valid_push_input):
    """POST /push should set content_type to application/json."""
    client.post("/push", json=valid_push_input)
    
    call_args = mock_gcs["blob"].upload_from_string.call_args
    assert call_args.kwargs["content_type"] == "application/json"


# ---------------------------------------------------------------------------
# Tests for /push endpoint - bias check handling
# ---------------------------------------------------------------------------

def test_push_handles_biased_content(mock_gcs, client, valid_push_input):
    """POST /push should succeed even when bias_check shows biased content."""
    valid_push_input["bias_check"]["is_biased"] = True
    valid_push_input["bias_check"]["similarity_score"] = 0.15
    
    response = client.post("/push", json=valid_push_input)
    
    assert response.status_code == 200
    assert response.json()["status"] == "pushed"


def test_push_handles_missing_bias_check(mock_gcs, client, valid_push_input):
    """POST /push should succeed without bias_check field."""
    del valid_push_input["bias_check"]
    
    response = client.post("/push", json=valid_push_input)
    
    assert response.status_code == 200
    assert response.json()["status"] == "pushed"


def test_push_handles_null_bias_check(mock_gcs, client, valid_push_input):
    """POST /push should succeed with bias_check=None."""
    valid_push_input["bias_check"] = None
    
    response = client.post("/push", json=valid_push_input)
    
    assert response.status_code == 200
    assert response.json()["status"] == "pushed"


def test_push_handles_null_similarity_score(mock_gcs, client, valid_push_input):
    """POST /push should handle bias_check with null similarity_score."""
    valid_push_input["bias_check"]["similarity_score"] = None
    
    response = client.post("/push", json=valid_push_input)
    
    assert response.status_code == 200


# ---------------------------------------------------------------------------
# Tests for /push endpoint - optional fields
# ---------------------------------------------------------------------------

def test_push_handles_missing_video_title(mock_gcs, client, valid_push_input):
    """POST /push should succeed without video_title."""
    del valid_push_input["video_title"]
    
    response = client.post("/push", json=valid_push_input)
    
    assert response.status_code == 200


def test_push_handles_empty_issues_list(mock_gcs, client, valid_push_input):
    """POST /push should succeed with empty issues list."""
    valid_push_input["issues"] = []
    
    response = client.post("/push", json=valid_push_input)
    
    assert response.status_code == 200


def test_push_handles_non_empty_issues_list(mock_gcs, client, valid_push_input):
    """POST /push should succeed even with validation issues (is_valid=False case)."""
    valid_push_input["is_valid"] = False
    valid_push_input["issues"] = ["Video summary is too short."]
    
    response = client.post("/push", json=valid_push_input)
    
    assert response.status_code == 200


# ---------------------------------------------------------------------------
# Tests for /push endpoint - error handling
# ---------------------------------------------------------------------------

def test_push_returns_500_on_gcs_error(mock_gcs, client, valid_push_input):
    """POST /push should return 500 when GCS upload fails."""
    mock_gcs["blob"].upload_from_string.side_effect = Exception("GCS connection failed")
    
    response = client.post("/push", json=valid_push_input)
    
    assert response.status_code == 500
    assert "GCS connection failed" in response.json()["detail"]


def test_push_returns_500_on_bucket_error(mock_gcs, client, valid_push_input):
    """POST /push should return 500 when bucket access fails."""
    mock_gcs["client"].bucket.side_effect = Exception("Bucket not found")
    
    response = client.post("/push", json=valid_push_input)
    
    assert response.status_code == 500


# ---------------------------------------------------------------------------
# Tests for /push endpoint - schema validation
# ---------------------------------------------------------------------------

def test_push_missing_video_id_returns_422(client):
    """POST /push without video_id should return 422."""
    response = client.post("/push", json={
        "video_summary": "Summary",
        "comment_summary": "Comments",
        "is_valid": True,
        "issues": []
    })
    
    assert response.status_code == 422


def test_push_missing_video_summary_returns_422(client):
    """POST /push without video_summary should return 422."""
    response = client.post("/push", json={
        "video_id": "abc123",
        "comment_summary": "Comments",
        "is_valid": True,
        "issues": []
    })
    
    assert response.status_code == 422


def test_push_missing_is_valid_returns_422(client):
    """POST /push without is_valid should return 422."""
    response = client.post("/push", json={
        "video_id": "abc123",
        "video_summary": "Summary",
        "comment_summary": "Comments",
        "issues": []
    })
    
    assert response.status_code == 422


def test_push_missing_issues_returns_422(client):
    """POST /push without issues should return 422."""
    response = client.post("/push", json={
        "video_id": "abc123",
        "video_summary": "Summary",
        "comment_summary": "Comments",
        "is_valid": True
    })
    
    assert response.status_code == 422
