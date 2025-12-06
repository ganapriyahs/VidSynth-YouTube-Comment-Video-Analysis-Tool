# changes for bias
from fastapi import FastAPI, Request 
from schemas import PushInput, PushOutput
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# FastAPI application instance
app = FastAPI(title="VidSynth Push Service")

@app.get("/")
def root():
    """Returns a simple message indicating the service is running."""
    return {"message": "VidSynth Push Service Running"}

@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "push_service"}

@app.post("/push", response_model=PushOutput)
async def push(request: PushInput, fastapi_request: Request):
    """
    Accepts the final validated data from the validate_service.
    Logs comprehensive information including video title, summaries, and bias detection results.
    """

    # Log raw request body for debugging
    try:
        raw_body = await fastapi_request.json()
        logger.debug(f"PUSH SERVICE: Received RAW request body: {raw_body}")
    except Exception as e:
        logger.error(f"PUSH SERVICE: Error reading raw request body: {e}")

    # Log video title if available
    video_title = request.video_title or "Unknown Title"
    logger.info(f"PUSH SERVICE: Processing video_id: {request.video_id}")
    logger.info(f"PUSH SERVICE: Video Title: '{video_title}'")

    # Check if data is valid
    if not request.is_valid:
        logger.warning(
            f"PUSH SERVICE: Received invalid data for {request.video_id}. "
            f"Discarding. Issues: {request.issues}"
        )
        
        # Log bias information if available (even for invalid data)
        if request.bias_check:
            bias = request.bias_check
            logger.warning(
                f"PUSH SERVICE: Bias detected - Similarity: {bias.similarity_score:.4f}, "
                f"Threshold: {bias.threshold}"
            )
        
        return PushOutput(status="discarded", video_id=request.video_id)

    # Data is valid - log comprehensive information
    logger.info(f"PUSH SERVICE: Pushing valid data for video_id: {request.video_id}")
    
    # Log bias check results if available
    if request.bias_check:
        bias = request.bias_check
        bias_status = "⚠️ BIASED" if bias.is_biased else "✓ UNBIASED"
        logger.info(f"PUSH SERVICE: Bias Check - {bias_status}")
        
        if bias.similarity_score is not None:
            logger.info(
                f"PUSH SERVICE: Similarity Score: {bias.similarity_score:.4f} "
                f"(Threshold: {bias.threshold})"
            )
        
        if bias.is_biased:
            logger.warning(
                f"PUSH SERVICE: LOW SIMILARITY DETECTED - Summary may not match video content"
            )
    else:
        logger.debug("PUSH SERVICE: No bias check information available")

    # Placeholder for Real-World Action
    # In production, you would:
    # - Save to database: db.save(request)
    # - Send to message queue: kafka.send(request)
    # - Store in cloud storage: gcs.upload(request)
    
    # Log the final summaries
    logger.info("=" * 80)
    logger.info(f"FINAL RESULTS FOR VIDEO: {request.video_id}")
    logger.info(f"Title: {video_title}")
    logger.info("-" * 80)
    logger.info("VIDEO SUMMARY:")
    logger.info(request.video_summary)
    logger.info("-" * 80)
    logger.info("COMMENT SUMMARY:")
    logger.info(request.comment_summary)
    logger.info("=" * 80)

    return PushOutput(status="pushed", video_id=request.video_id)