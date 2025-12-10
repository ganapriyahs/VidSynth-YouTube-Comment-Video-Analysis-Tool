"""
Tests for the gateway service.
"""
import os
import sys
import json

# ---------------------------------------------------------------------------
# Path and environment setup (must come before importing service code)
# ---------------------------------------------------------------------------

# Set required environment variable before importing main
os.environ["AIRFLOW_WEBSERVER_URL"] = "https://fake-airflow.example.com"

# Add gateway service directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "gateway_service"))

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from main import app, RESULTS_BUCKET, DAG_ID, AIRFLOW_WEBSERVER_URL


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def mock_gcs():
    """Mock Google Cloud Storage client."""
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


@pytest.fixture
def mock_auth():
    """Mock Google auth for getting access token."""
    with patch("main.google.auth.default") as mock_default:
        mock_credentials = MagicMock()
        mock_credentials.token = "fake-access-token-12345"
        mock_default.return_value = (mock_credentials, "project-id")
        
        yield {
            "default": mock_default,
            "credentials": mock_credentials
        }


@pytest.fixture
def mock_requests():
    """Mock requests library for Airflow API calls."""
    with patch("main.requests.post") as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '{"dag_run_id": "manual__2024-01-01"}'
        mock_post.return_value = mock_response
        
        yield {
            "post": mock_post,
            "response": mock_response
        }


# ---------------------------------------------------------------------------
# Tests for root endpoint
# ---------------------------------------------------------------------------

def test_root_returns_200(client):
    """GET / should return 200 with service status message."""
    response = client.get("/")
    
    assert response.status_code == 200
    assert response.json() == {"message": "VidSynth Gateway is Running (Fast Mode)"}


# ---------------------------------------------------------------------------
# Tests for /summarize endpoint - success cases
# ---------------------------------------------------------------------------

def test_summarize_returns_started_status(mock_gcs, mock_auth, mock_requests, client):
    """POST /summarize should return status='started' on success."""
    mock_gcs["blob"].exists.return_value = False
    
    response = client.post("/summarize", json={"video_id": "abc123"})
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "started"
    assert data["video_id"] == "abc123"
    assert "message" in data


def test_summarize_uses_correct_bucket(mock_gcs, mock_auth, mock_requests, client):
    """POST /summarize should access the configured results bucket."""
    mock_gcs["blob"].exists.return_value = False
    
    client.post("/summarize", json={"video_id": "abc123"})
    
    mock_gcs["client"].bucket.assert_called_with(RESULTS_BUCKET)


def test_summarize_checks_for_stale_data(mock_gcs, mock_auth, mock_requests, client):
    """POST /summarize should check if blob exists."""
    mock_gcs["blob"].exists.return_value = False
    
    client.post("/summarize", json={"video_id": "abc123"})
    
    mock_gcs["bucket"].blob.assert_called_with("abc123.json")
    mock_gcs["blob"].exists.assert_called_once()


def test_summarize_deletes_stale_data_if_exists(mock_gcs, mock_auth, mock_requests, client):
    """POST /summarize should delete existing blob before triggering."""
    mock_gcs["blob"].exists.return_value = True
    
    client.post("/summarize", json={"video_id": "abc123"})
    
    mock_gcs["blob"].delete.assert_called_once()


def test_summarize_skips_delete_if_no_stale_data(mock_gcs, mock_auth, mock_requests, client):
    """POST /summarize should not delete if blob doesn't exist."""
    mock_gcs["blob"].exists.return_value = False
    
    client.post("/summarize", json={"video_id": "abc123"})
    
    mock_gcs["blob"].delete.assert_not_called()


# ---------------------------------------------------------------------------
# Tests for /summarize endpoint - Airflow API interaction
# ---------------------------------------------------------------------------

def test_summarize_calls_airflow_api(mock_gcs, mock_auth, mock_requests, client):
    """POST /summarize should call Airflow REST API."""
    mock_gcs["blob"].exists.return_value = False
    
    client.post("/summarize", json={"video_id": "abc123"})
    
    mock_requests["post"].assert_called_once()


def test_summarize_uses_correct_airflow_endpoint(mock_gcs, mock_auth, mock_requests, client):
    """POST /summarize should call the correct Airflow DAG endpoint."""
    mock_gcs["blob"].exists.return_value = False
    
    client.post("/summarize", json={"video_id": "abc123"})
    
    expected_endpoint = f"{AIRFLOW_WEBSERVER_URL}/api/v1/dags/{DAG_ID}/dagRuns"
    call_args = mock_requests["post"].call_args
    assert call_args[0][0] == expected_endpoint


def test_summarize_sends_video_link_in_payload(mock_gcs, mock_auth, mock_requests, client):
    """POST /summarize should send video_link in DAG conf."""
    mock_gcs["blob"].exists.return_value = False
    
    client.post("/summarize", json={"video_id": "abc123"})
    
    call_args = mock_requests["post"].call_args
    payload = call_args.kwargs["json"]
    assert payload["conf"]["video_link"] == "https://www.youtube.com/watch?v=abc123"


def test_summarize_uses_bearer_token(mock_gcs, mock_auth, mock_requests, client):
    """POST /summarize should use Bearer token from Google auth."""
    mock_gcs["blob"].exists.return_value = False
    
    client.post("/summarize", json={"video_id": "abc123"})
    
    call_args = mock_requests["post"].call_args
    headers = call_args.kwargs["headers"]
    assert headers["Authorization"] == "Bearer fake-access-token-12345"
    assert headers["Content-Type"] == "application/json"


def test_summarize_refreshes_credentials(mock_gcs, mock_auth, mock_requests, client):
    """POST /summarize should refresh credentials before getting token."""
    mock_gcs["blob"].exists.return_value = False
    
    client.post("/summarize", json={"video_id": "abc123"})
    
    mock_auth["credentials"].refresh.assert_called_once()


# ---------------------------------------------------------------------------
# Tests for /summarize endpoint - error handling
# ---------------------------------------------------------------------------

def test_summarize_returns_500_when_airflow_url_not_configured(mock_gcs, mock_auth, mock_requests, client):
    """POST /summarize should return 500 when AIRFLOW_WEBSERVER_URL is not set."""
    import main
    original_url = main.AIRFLOW_WEBSERVER_URL
    main.AIRFLOW_WEBSERVER_URL = None
    
    try:
        response = client.post("/summarize", json={"video_id": "abc123"})
        
        assert response.status_code == 500
        assert "AIRFLOW_WEBSERVER_URL not configured" in response.json()["detail"]
    finally:
        main.AIRFLOW_WEBSERVER_URL = original_url


def test_summarize_returns_500_on_airflow_error(mock_gcs, mock_auth, mock_requests, client):
    """POST /summarize should return 500 when Airflow API fails."""
    mock_gcs["blob"].exists.return_value = False
    mock_requests["response"].status_code = 403
    mock_requests["response"].text = "Forbidden"
    
    response = client.post("/summarize", json={"video_id": "abc123"})
    
    assert response.status_code == 500
    assert "Airflow refused trigger" in response.json()["detail"]


def test_summarize_returns_500_on_gcs_error(mock_gcs, mock_auth, mock_requests, client):
    """POST /summarize should return 500 when GCS access fails."""
    mock_gcs["client"].bucket.side_effect = Exception("GCS error")
    
    response = client.post("/summarize", json={"video_id": "abc123"})
    
    assert response.status_code == 500


def test_summarize_returns_500_on_auth_error(mock_gcs, mock_auth, mock_requests, client):
    """POST /summarize should return 500 when auth fails."""
    mock_gcs["blob"].exists.return_value = False
    mock_auth["credentials"].refresh.side_effect = Exception("Auth failed")
    
    response = client.post("/summarize", json={"video_id": "abc123"})
    
    assert response.status_code == 500


# ---------------------------------------------------------------------------
# Tests for /summarize endpoint - schema validation
# ---------------------------------------------------------------------------

def test_summarize_missing_video_id_returns_422(client):
    """POST /summarize without video_id should return 422."""
    response = client.post("/summarize", json={})
    
    assert response.status_code == 422


def test_summarize_empty_body_returns_422(client):
    """POST /summarize with empty body should return 422."""
    response = client.post("/summarize")
    
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Tests for /result/{video_id} endpoint - success cases
# ---------------------------------------------------------------------------

def test_result_returns_data_when_ready(mock_gcs, client):
    """GET /result/{video_id} should return data when blob exists."""
    mock_gcs["blob"].exists.return_value = True
    mock_gcs["blob"].download_as_text.return_value = json.dumps({
        "status": "ready",
        "video_id": "abc123",
        "data": {
            "video_summary": "This is the summary.",
            "comment_summary": "These are the comments."
        }
    })
    
    response = client.get("/result/abc123")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert data["video_id"] == "abc123"
    assert "data" in data


def test_result_returns_processing_when_not_ready(mock_gcs, client):
    """GET /result/{video_id} should return status='processing' when blob doesn't exist."""
    mock_gcs["blob"].exists.return_value = False
    
    response = client.get("/result/abc123")
    
    assert response.status_code == 200
    assert response.json() == {"status": "processing"}


def test_result_uses_correct_bucket(mock_gcs, client):
    """GET /result/{video_id} should access the configured results bucket."""
    mock_gcs["blob"].exists.return_value = False
    
    client.get("/result/abc123")
    
    mock_gcs["client"].bucket.assert_called_with(RESULTS_BUCKET)


def test_result_uses_correct_blob_name(mock_gcs, client):
    """GET /result/{video_id} should look for {video_id}.json blob."""
    mock_gcs["blob"].exists.return_value = False
    
    client.get("/result/test_video_xyz")
    
    mock_gcs["bucket"].blob.assert_called_with("test_video_xyz.json")


# ---------------------------------------------------------------------------
# Tests for /result/{video_id} endpoint - error handling
# ---------------------------------------------------------------------------

def test_result_returns_500_on_gcs_error(mock_gcs, client):
    """GET /result/{video_id} should return 500 when GCS fails."""
    mock_gcs["client"].bucket.side_effect = Exception("GCS connection failed")
    
    response = client.get("/result/abc123")
    
    assert response.status_code == 500
    assert "GCS connection failed" in response.json()["detail"]


def test_result_returns_500_on_download_error(mock_gcs, client):
    """GET /result/{video_id} should return 500 when download fails."""
    mock_gcs["blob"].exists.return_value = True
    mock_gcs["blob"].download_as_text.side_effect = Exception("Download failed")
    
    response = client.get("/result/abc123")
    
    assert response.status_code == 500


def test_result_returns_500_on_invalid_json(mock_gcs, client):
    """GET /result/{video_id} should return 500 when blob contains invalid JSON."""
    mock_gcs["blob"].exists.return_value = True
    mock_gcs["blob"].download_as_text.return_value = "not valid json"
    
    response = client.get("/result/abc123")
    
    assert response.status_code == 500