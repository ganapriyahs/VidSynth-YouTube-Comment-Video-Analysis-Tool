"""
Tests for the validate service.
"""
import os
import sys

# ---------------------------------------------------------------------------
# Path and environment setup (must come before importing service code)
# ---------------------------------------------------------------------------

# Disable bias check by default for most tests (avoids loading heavy ML model)
os.environ["ENABLE_BIAS_CHECK"] = "false"

# Add validate service directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "validate_service"))

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    # Import here to ensure env vars are set first
    from main import app
    return TestClient(app)


@pytest.fixture
def valid_llm_output():
    """Valid input that should pass all validation checks."""
    return {
        "video_id": "abc123",
        "video_summary": "This is a sufficiently long video summary that discusses the main topics covered in the video content.",
        "comment_summary": "This is a sufficiently long comment summary that captures the sentiment and themes from viewer comments.",
        "video_title": "Test Video Title"
    }


# ---------------------------------------------------------------------------
# Tests for root endpoint
# ---------------------------------------------------------------------------

def test_root_returns_200(client):
    """GET / should return 200 with service status message."""
    response = client.get("/")
    
    assert response.status_code == 200
    assert response.json() == {"message": "VidSynth Validate Service Running"}


# ---------------------------------------------------------------------------
# Tests for /validate endpoint - valid input (bias check disabled)
# ---------------------------------------------------------------------------

def test_validate_passes_with_valid_input(client, valid_llm_output):
    """POST /validate with valid summaries should return is_valid=True."""
    response = client.post("/validate", json=valid_llm_output)
    
    assert response.status_code == 200
    data = response.json()
    assert data["is_valid"] == True
    assert data["issues"] == []
    assert data["video_id"] == "abc123"
    assert data["video_summary"] == valid_llm_output["video_summary"]
    assert data["comment_summary"] == valid_llm_output["comment_summary"]


def test_validate_returns_all_fields(client, valid_llm_output):
    """POST /validate should return all expected fields in response."""
    response = client.post("/validate", json=valid_llm_output)
    
    assert response.status_code == 200
    data = response.json()
    
    # Check all required fields are present
    assert "video_id" in data
    assert "video_summary" in data
    assert "comment_summary" in data
    assert "is_valid" in data
    assert "issues" in data
    assert "bias_check" in data


# ---------------------------------------------------------------------------
# Tests for /validate endpoint - missing summaries
# ---------------------------------------------------------------------------

def test_validate_fails_when_video_summary_missing(client, valid_llm_output):
    """POST /validate with empty video_summary should fail."""
    valid_llm_output["video_summary"] = ""
    
    response = client.post("/validate", json=valid_llm_output)
    
    assert response.status_code == 200
    data = response.json()
    assert data["is_valid"] == False
    assert "Video summary is missing." in data["issues"]


def test_validate_fails_when_video_summary_is_placeholder(client, valid_llm_output):
    """POST /validate with 'No transcript available' should fail."""
    valid_llm_output["video_summary"] = "No transcript available for this video."
    
    response = client.post("/validate", json=valid_llm_output)
    
    assert response.status_code == 200
    data = response.json()
    assert data["is_valid"] == False
    assert "Video summary is missing." in data["issues"]


def test_validate_fails_when_comment_summary_missing(client, valid_llm_output):
    """POST /validate with empty comment_summary should fail."""
    valid_llm_output["comment_summary"] = ""
    
    response = client.post("/validate", json=valid_llm_output)
    
    assert response.status_code == 200
    data = response.json()
    assert data["is_valid"] == False
    assert "Comment summary is missing." in data["issues"]


def test_validate_fails_when_comment_summary_is_placeholder(client, valid_llm_output):
    """POST /validate with 'No comments available' should fail."""
    valid_llm_output["comment_summary"] = "No comments available."
    
    response = client.post("/validate", json=valid_llm_output)
    
    assert response.status_code == 200
    data = response.json()
    assert data["is_valid"] == False
    assert "Comment summary is missing." in data["issues"]


# ---------------------------------------------------------------------------
# Tests for /validate endpoint - summaries too short
# ---------------------------------------------------------------------------

def test_validate_fails_when_video_summary_too_short(client, valid_llm_output):
    """POST /validate with video_summary under 10 words should fail."""
    valid_llm_output["video_summary"] = "Too short."
    
    response = client.post("/validate", json=valid_llm_output)
    
    assert response.status_code == 200
    data = response.json()
    assert data["is_valid"] == False
    assert "Video summary is too short." in data["issues"]


def test_validate_fails_when_comment_summary_too_short(client, valid_llm_output):
    """POST /validate with comment_summary under 10 words should fail."""
    valid_llm_output["comment_summary"] = "Brief."
    
    response = client.post("/validate", json=valid_llm_output)
    
    assert response.status_code == 200
    data = response.json()
    assert data["is_valid"] == False
    assert "Comment summary is too short." in data["issues"]


def test_validate_accumulates_multiple_issues(client, valid_llm_output):
    """POST /validate should report all issues found."""
    valid_llm_output["video_summary"] = ""
    valid_llm_output["comment_summary"] = "Short."
    
    response = client.post("/validate", json=valid_llm_output)
    
    assert response.status_code == 200
    data = response.json()
    assert data["is_valid"] == False
    assert len(data["issues"]) == 2
    assert "Video summary is missing." in data["issues"]
    assert "Comment summary is too short." in data["issues"]


# ---------------------------------------------------------------------------
# Tests for /validate endpoint - schema validation
# ---------------------------------------------------------------------------

def test_validate_missing_video_id_returns_422(client):
    """POST /validate without video_id should return 422."""
    response = client.post("/validate", json={
        "video_summary": "Some summary",
        "comment_summary": "Some comments"
    })
    
    assert response.status_code == 422


def test_validate_missing_video_summary_field_returns_422(client):
    """POST /validate without video_summary field should return 422."""
    response = client.post("/validate", json={
        "video_id": "abc123",
        "comment_summary": "Some comments"
    })
    
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Tests for /validate endpoint - with bias check enabled
# ---------------------------------------------------------------------------

class TestValidateWithBiasCheck:
    """Tests for validation with bias checking enabled."""
    
    def test_validate_runs_bias_check_when_enabled(self, valid_llm_output):
        """Bias check should run when ENABLE_BIAS_CHECK is true."""
        # Reload module with bias check enabled
        import importlib
        import main
        importlib.reload(main)
        main.ENABLE_BIAS_CHECK = True
        
        # Patch AFTER reload
        with patch.object(main, "get_bias_monitor") as mock_get:
            mock_monitor = MagicMock()
            mock_get.return_value = mock_monitor
            mock_monitor.check_bias.return_value = {
                "similarity_score": 0.75,
                "is_biased": False,
                "threshold": 0.30,
                "summary_preview": valid_llm_output["video_summary"][:100],
                "video_title": valid_llm_output["video_title"]
            }
            
            client = TestClient(main.app)
            response = client.post("/validate", json=valid_llm_output)
            
            assert response.status_code == 200
            mock_monitor.check_bias.assert_called_once()
    
    def test_validate_adds_issue_when_bias_detected(self, valid_llm_output):
        """Bias detection should add issue when similarity is low."""
        import importlib
        import main
        importlib.reload(main)
        main.ENABLE_BIAS_CHECK = True
        
        with patch.object(main, "get_bias_monitor") as mock_get:
            mock_monitor = MagicMock()
            mock_get.return_value = mock_monitor
            mock_monitor.check_bias.return_value = {
                "similarity_score": 0.15,
                "is_biased": True,
                "threshold": 0.30,
                "summary_preview": "Unrelated content...",
                "video_title": valid_llm_output["video_title"]
            }
            
            client = TestClient(main.app)
            response = client.post("/validate", json=valid_llm_output)
            
            assert response.status_code == 200
            data = response.json()
            assert data["is_valid"] == False
            assert any("bias" in issue.lower() for issue in data["issues"])
    
    def test_validate_passes_when_no_bias_detected(self, valid_llm_output):
        """Validation should pass when bias check passes."""
        import importlib
        import main
        importlib.reload(main)
        main.ENABLE_BIAS_CHECK = True
        
        with patch.object(main, "get_bias_monitor") as mock_get:
            mock_monitor = MagicMock()
            mock_get.return_value = mock_monitor
            mock_monitor.check_bias.return_value = {
                "similarity_score": 0.85,
                "is_biased": False,
                "threshold": 0.30,
                "summary_preview": valid_llm_output["video_summary"][:100],
                "video_title": valid_llm_output["video_title"]
            }
            
            client = TestClient(main.app)
            response = client.post("/validate", json=valid_llm_output)
            
            assert response.status_code == 200
            data = response.json()
            assert data["is_valid"] == True
            assert data["bias_check"] is not None
            assert data["bias_check"]["is_biased"] == False
    
    def test_validate_includes_bias_check_result(self, valid_llm_output):
        """Response should include bias_check result object."""
        import importlib
        import main
        importlib.reload(main)
        main.ENABLE_BIAS_CHECK = True
        
        with patch.object(main, "get_bias_monitor") as mock_get:
            mock_monitor = MagicMock()
            mock_get.return_value = mock_monitor
            mock_monitor.check_bias.return_value = {
                "similarity_score": 0.65,
                "is_biased": False,
                "threshold": 0.30,
                "summary_preview": "Preview text...",
                "video_title": "Test Title"
            }
            
            client = TestClient(main.app)
            response = client.post("/validate", json=valid_llm_output)
            
            assert response.status_code == 200
            data = response.json()
            assert data["bias_check"] is not None
            assert "similarity_score" in data["bias_check"]
            assert "is_biased" in data["bias_check"]
            assert "threshold" in data["bias_check"]


# ---------------------------------------------------------------------------
# Tests for BiasMonitor class
# ---------------------------------------------------------------------------

class TestBiasMonitor:
    """Unit tests for the BiasMonitor class."""
    
    @patch("bias_monitor.SentenceTransformer")
    def test_check_bias_returns_not_biased_for_high_similarity(self, mock_transformer):
        """check_bias should return is_biased=False when similarity is high."""
        mock_model = MagicMock()
        mock_transformer.return_value = mock_model
        
        # Mock embeddings that will produce high similarity
        mock_model.encode.side_effect = [
            [[1.0, 0.0, 0.0]],  # title embedding
            [[0.9, 0.1, 0.0]]   # summary embedding (similar)
        ]
        
        from bias_monitor import BiasMonitor
        monitor = BiasMonitor(bias_threshold=0.30)
        
        result = monitor.check_bias(
            video_title="Python Tutorial",
            generated_summary="This tutorial covers Python programming basics."
        )
        
        assert result["is_biased"] == False
        assert result["similarity_score"] > 0.30
    
    @patch("bias_monitor.SentenceTransformer")
    def test_check_bias_returns_biased_for_low_similarity(self, mock_transformer):
        """check_bias should return is_biased=True when similarity is low."""
        mock_model = MagicMock()
        mock_transformer.return_value = mock_model
        
        # Mock embeddings that will produce low similarity
        mock_model.encode.side_effect = [
            [[1.0, 0.0, 0.0]],  # title embedding
            [[0.0, 1.0, 0.0]]   # summary embedding (orthogonal = 0 similarity)
        ]
        
        from bias_monitor import BiasMonitor
        monitor = BiasMonitor(bias_threshold=0.30)
        
        result = monitor.check_bias(
            video_title="Python Tutorial",
            generated_summary="Completely unrelated content about cooking."
        )
        
        assert result["is_biased"] == True
        assert result["similarity_score"] < 0.30
    
    @patch("bias_monitor.SentenceTransformer")
    def test_check_bias_skips_empty_title(self, mock_transformer):
        """check_bias should skip when title is empty."""
        mock_model = MagicMock()
        mock_transformer.return_value = mock_model
        
        from bias_monitor import BiasMonitor
        monitor = BiasMonitor()
        
        result = monitor.check_bias(
            video_title="",
            generated_summary="Some summary content."
        )
        
        assert result["summary_type"] == "skipped"
        assert result["is_biased"] == False
        mock_model.encode.assert_not_called()
    
    @patch("bias_monitor.SentenceTransformer")
    def test_check_bias_marks_empty_summary_as_biased(self, mock_transformer):
        """check_bias should mark empty summary as biased."""
        mock_model = MagicMock()
        mock_transformer.return_value = mock_model
        
        from bias_monitor import BiasMonitor
        monitor = BiasMonitor()
        
        result = monitor.check_bias(
            video_title="Python Tutorial",
            generated_summary=""
        )
        
        assert result["is_biased"] == True
        assert result["similarity_score"] == 0.0
    
    @patch("bias_monitor.SentenceTransformer")
    def test_check_bias_skips_placeholder_messages(self, mock_transformer):
        """check_bias should skip placeholder messages."""
        mock_model = MagicMock()
        mock_transformer.return_value = mock_model
        
        from bias_monitor import BiasMonitor
        monitor = BiasMonitor()
        
        result = monitor.check_bias(
            video_title="Some Title",
            generated_summary="No transcript available"
        )
        
        assert result["summary_type"] == "skipped"
        assert result["skip_reason"] == "Placeholder message"
    
    @patch("bias_monitor.SentenceTransformer")
    def test_update_threshold_changes_threshold(self, mock_transformer):
        """update_threshold should update the bias_threshold value."""
        mock_transformer.return_value = MagicMock()
        
        from bias_monitor import BiasMonitor
        monitor = BiasMonitor(bias_threshold=0.30)
        
        monitor.update_threshold(0.50)
        
        assert monitor.bias_threshold == 0.50
    
    @patch("bias_monitor.SentenceTransformer")
    def test_update_threshold_rejects_invalid_values(self, mock_transformer):
        """update_threshold should reject values outside 0-1 range."""
        mock_transformer.return_value = MagicMock()
        
        from bias_monitor import BiasMonitor
        monitor = BiasMonitor()
        
        with pytest.raises(ValueError):
            monitor.update_threshold(1.5)
        
        with pytest.raises(ValueError):
            monitor.update_threshold(-0.1)
