# Import necessary libraries
from fastapi import FastAPI, HTTPException 
from schemas import VideoIdInput, PreprocessOutput
from youtube_client import youtube_client  
import logging  

# basic logging 
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
app = FastAPI(title="VidSynth Preprocess Service") 

@app.get("/")
def root():
    """Returns a simple message indicating the service is running."""
    return {"message": "VidSynth Preprocess Service Running"}

@app.post("/preprocess", response_model=PreprocessOutput)
def preprocess(request: VideoIdInput):
    """
    Accepts a POST request containing a YouTube video ID,
    fetches the transcript, comments, AND TITLE for that video,
    and returns the fetched data.
    """
    video_id = request.video_id
    logger.info(f"PREPROCESS SERVICE: Received request for video_id: {video_id}")

    try:
        data = youtube_client.get_video_data(video_id)
    except Exception as e:
        logger.error(f"An unexpected error occurred in get_video_data for {video_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error fetching data: {e}")

    transcript = data.get("transcript", "")
    comments = data.get("comments", "")
    video_title = data.get("video_title", "Unknown Title") 

    if not transcript and not comments:
        logger.warning(f"Could not retrieve any data (transcript or comments) for video_id: {video_id}")
        logger.info(f"PREPROCESS SERVICE: No data found for video_id: {video_id}, returning empty strings.")
    else:
         logger.info(f"PREPROCESS SERVICE: Successfully fetched data for video_id: {video_id}")
         logger.info(f"PREPROCESS SERVICE: Video title: '{video_title}'") 

    return PreprocessOutput(
        video_id=video_id,
        transcript=transcript,
        comments=comments,
        video_title=video_title 
    )