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


@app.post("/push", response_model=PushOutput)
async def push(request: PushInput, fastapi_request: Request): # Add fastapi_request
    """
    Accepts the final validated data from the validate_service.
    Logs the raw request body for debugging.
    If the data is marked as valid, it logs the summaries.
    If invalid, it logs that the data is discarded.
    Returns a status indicating the outcome ('pushed' or 'discarded').
    """

    try:
        raw_body = await fastapi_request.json()
        logger.info(f"PUSH SERVICE: Received RAW request body: {raw_body}")
    except Exception as e:
        logger.error(f"PUSH SERVICE: Error reading raw request body: {e}")

    if not request.is_valid:
        logger.warning(f"PUSH SERVICE: Received invalid data for {request.video_id}. Discarding. Issues: {request.issues}")
        return PushOutput(status="discarded", video_id=request.video_id)

    logger.info(f"PUSH SERVICE: Pushing valid data for video_id: {request.video_id}")

    # Placeholder for Real-World Action
    # db.save(...)

    logger.info(f"--- Final Video Summary ({request.video_id}) ---")
    logger.info(request.video_summary)
    logger.info(f"--- Final Comment Summary ({request.video_id}) ---")
    logger.info(request.comment_summary)
    logger.info("--- End Summaries ---")

    return PushOutput(status="pushed", video_id=request.video_id)

