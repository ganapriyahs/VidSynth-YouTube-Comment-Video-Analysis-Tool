# For bias changes
"""
VidSynth Validate Service
Validates generated summaries with basic checks and bias detection.
"""

import logging
import os
from typing import List
from fastapi import FastAPI, HTTPException
from schemas import LLMOutput, ValidateOutput, BiasCheckResult
from bias_monitor import get_bias_monitor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize the FastAPI application instance
app = FastAPI(
    title="VidSynth Validate Service",
    description="Validates LLM-generated summaries with bias detection",
    version="1.0.0"
)

# Configuration
MIN_SUMMARY_LENGTH = int(os.getenv("MIN_SUMMARY_LENGTH", "10"))
ENABLE_BIAS_CHECK = os.getenv("ENABLE_BIAS_CHECK", "true").lower() == "true"

@app.on_event("startup")
async def startup_event():
    """Initialize resources on startup."""
    logger.info("VidSynth Validate Service starting up...")
    logger.info(f"Configuration: MIN_SUMMARY_LENGTH={MIN_SUMMARY_LENGTH}, ENABLE_BIAS_CHECK={ENABLE_BIAS_CHECK}")
    
    # Pre-load bias monitor model
    if ENABLE_BIAS_CHECK:
        try:
            bias_monitor = get_bias_monitor()
            logger.info("Bias monitor initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize bias monitor: {e}")
            logger.warning("Continuing without bias detection")

@app.get("/")
def root():
    """Health check endpoint."""
    return {
        "message": "VidSynth Validate Service Running",
        "version": "1.0.0",
        "bias_detection_enabled": ENABLE_BIAS_CHECK
    }

@app.get("/health")
def health_check():
    """Detailed health check endpoint."""
    health_status = {
        "status": "healthy",
        "service": "validate_service",
        "bias_detection": ENABLE_BIAS_CHECK
    }
    
    if ENABLE_BIAS_CHECK:
        try:
            bias_monitor = get_bias_monitor()
            health_status["bias_monitor"] = "ready"
        except Exception as e:
            health_status["bias_monitor"] = f"error: {str(e)}"
            health_status["status"] = "degraded"
    
    return health_status

@app.post("/validate", response_model=ValidateOutput)
def validate(request: LLMOutput):
    """
    Validates generated summaries with basic checks and bias detection.
    """
    logger.info(f"VALIDATE SERVICE: Starting validation for video_id={request.video_id}")
    
    issues = []
    bias_check_result = None
    
    try:
        # --- Basic Validation Logic ---
        logger.debug("Performing basic validation checks...")
        
        # Check video summary
        if not request.video_summary or request.video_summary in ["No transcript available."]:
            issues.append("Video summary is missing or unavailable.")
        elif len(request.video_summary.split()) < MIN_SUMMARY_LENGTH:
            issues.append(f"Video summary is too short (less than {MIN_SUMMARY_LENGTH} words).")
        
        # Check comment summary
        if not request.comment_summary or request.comment_summary in ["No comments available."]:
            issues.append("Comment summary is missing or unavailable.")
        elif len(request.comment_summary.split()) < MIN_SUMMARY_LENGTH:
            issues.append(f"Comment summary is too short (less than {MIN_SUMMARY_LENGTH} words).")
        
        # --- Bias Detection ---
        if ENABLE_BIAS_CHECK and request.video_title:
            logger.info("Performing bias detection...")
            
            try:
                bias_monitor = get_bias_monitor()
                
                # Check bias for video summary
                bias_result = bias_monitor.check_bias(
                    video_title=request.video_title,
                    generated_summary=request.video_summary,
                    summary_type="video"
                )
                
                # Create BiasCheckResult for response
                bias_check_result = BiasCheckResult(
                    similarity_score=bias_result.get("similarity_score"),
                    is_biased=bias_result.get("is_biased", False),
                    threshold=bias_result.get("threshold", 0.30),
                    summary_preview=bias_result.get("summary_preview", ""),
                    video_title=bias_result.get("video_title")
                )
                
                # Add to issues if biased
                if bias_result.get("is_biased"):
                    similarity = bias_result.get("similarity_score", 0)
                    issues.append(
                        f"Potential bias detected: Low similarity ({similarity:.2f}) "
                        f"between video title and summary."
                    )
                    logger.warning(
                        f"BIAS DETECTED for video_id={request.video_id}: "
                        f"Similarity={similarity:.4f}"
                    )
                
            except Exception as e:
                logger.error(f"Bias detection failed: {e}", exc_info=True)
                issues.append(f"Bias detection failed: {str(e)}")
        
        elif ENABLE_BIAS_CHECK and not request.video_title:
            logger.warning("Bias check enabled but no video_title provided")
            issues.append("Cannot perform bias check: video_title not provided")
        
        # --- Determine Overall Validity ---
        is_valid = len(issues) == 0
        
        logger.info(
            f"VALIDATE SERVICE: Validation complete for video_id={request.video_id}. "
            f"Valid: {is_valid}, Issues: {len(issues)}"
        )
        
        return ValidateOutput(
            video_id=request.video_id,
            video_summary=request.video_summary,
            comment_summary=request.comment_summary,
            is_valid=is_valid,
            issues=issues,
            bias_check=bias_check_result
        )
    
    except Exception as e:
        logger.error(f"Validation error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")