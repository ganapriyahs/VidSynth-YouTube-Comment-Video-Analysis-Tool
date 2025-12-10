import os
import json
import logging
from fastapi import FastAPI, HTTPException
from google.cloud import storage
from schemas import PushInput, PushOutput

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="VidSynth Push Service")

# CONFIGURATION
BUCKET_NAME = "vidsynth_results" 

@app.get("/")
def root():
    return {"message": "VidSynth Push Service Running (FastAPI)"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "push_service"}

@app.post("/push", response_model=PushOutput)
def push_to_storage(request: PushInput):
    """
    Receives validated data, logs Bias Detection results, and saves 
    the summary to GCS in the strict JSON structure required by the Extension.
    """
    logger.info(f"PUSH: Received request for video_id: {request.video_id}")

    try:
        video_title = request.video_title or "Unknown Title"
        
        if request.bias_check:
            bias = request.bias_check

            status_icon = "⚠️ BIASED" if bias.is_biased else "✅ UNBIASED"
            score_display = f"{bias.similarity_score:.2f}" if bias.similarity_score is not None else "N/A"
            
            logger.info(f"PUSH: Video '{video_title}' | Result: {status_icon} (Score: {score_display})")
            
            if bias.is_biased:
                logger.warning("PUSH: Low similarity detected between title and summary.")
        else:
            logger.info(f"PUSH: Processing '{video_title}' (No bias data available)")

        final_output = {
            "status": "ready",
            "video_id": request.video_id,
            "data": {
                "video_summary": request.video_summary,
                "comment_summary": request.comment_summary
            }
        }

        filename = f"{request.video_id}.json"
        storage_client = storage.Client()
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(filename)

        logger.info(f"PUSH: Saving {filename} to bucket...")
        
        blob.upload_from_string(
            data=json.dumps(final_output),
            content_type="application/json"
        )

        logger.info("PUSH: Success.")
        return PushOutput(status="pushed", video_id=request.video_id)

    except Exception as e:
        logger.error(f"PUSH ERROR: {e}")
        raise HTTPException(status_code=500, detail=str(e))