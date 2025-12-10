import logging
import os
from fastapi import FastAPI, HTTPException
from schemas import LLMOutput, ValidateOutput, BiasCheckResult
from bias_monitor import get_bias_monitor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="VidSynth Validate Service")

# Configuration
ENABLE_BIAS_CHECK = os.getenv("ENABLE_BIAS_CHECK", "true").lower() == "true"
MIN_SUMMARY_LENGTH = 10

@app.on_event("startup")
async def startup_event():
    """Initialize resources on startup."""
    logger.info("VidSynth Validate Service starting up...")
    
    if ENABLE_BIAS_CHECK:
        try:
            get_bias_monitor()
            logger.info("✅ Bias monitor initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize bias monitor: {e}")

@app.get("/")
def root():
    return {"message": "VidSynth Validate Service Running"}

@app.post("/validate", response_model=ValidateOutput)
def validate(request: LLMOutput):
    logger.info(f"VALIDATE: Starting validation for video_id={request.video_id}")
    
    issues = []
    bias_check_result = None

    if not request.video_summary or "No transcript available" in request.video_summary:
        issues.append("Video summary is missing.")
    elif len(request.video_summary.split()) < MIN_SUMMARY_LENGTH:
        issues.append("Video summary is too short.")
        
    if not request.comment_summary or "No comments available" in request.comment_summary:
        issues.append("Comment summary is missing.")
    elif len(request.comment_summary.split()) < MIN_SUMMARY_LENGTH:
        issues.append("Comment summary is too short.")

    if ENABLE_BIAS_CHECK and request.video_title:
        logger.info(f"Performing bias detection against title: '{request.video_title}'")
        try:
            monitor = get_bias_monitor()
            
            bias_result = monitor.check_bias(
                video_title=request.video_title,
                generated_summary=request.video_summary
            )
            
            # Create Result Object
            bias_check_result = BiasCheckResult(
                similarity_score=bias_result.get("similarity_score"),
                is_biased=bias_result.get("is_biased", False),
                threshold=bias_result.get("threshold", 0.30),
                summary_preview=bias_result.get("summary_preview", ""),
                video_title=bias_result.get("video_title")
            )
            
            if bias_result.get("is_biased"):
                score = bias_result.get("similarity_score", 0)
                issues.append(f"Potential bias detected: Low similarity ({score:.2f}) between title and summary.")
                logger.warning(f"⚠️ BIAS DETECTED: Score {score:.2f} < 0.30")
            else:
                logger.info("✅ Bias Check Passed.")
                
        except Exception as e:
            logger.error(f"Bias detection failed: {e}")
            issues.append(f"Bias check error: {str(e)}")

    is_valid = len(issues) == 0
    
    return ValidateOutput(
        video_id=request.video_id,
        video_summary=request.video_summary,
        comment_summary=request.comment_summary,
        is_valid=is_valid,
        issues=issues,
        bias_check=bias_check_result
    )