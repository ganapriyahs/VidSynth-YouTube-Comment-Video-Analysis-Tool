# Import necessary libraries
from fastapi import FastAPI, HTTPException 
from schemas import ReadRequest, ReadOutput  
from urllib.parse import urlparse, parse_qs 
import logging 

# Initialize the FastAPI application instance
app = FastAPI(title="VidSynth Read Service") 

# basic logging 
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# helper function to extract the YouTube video ID from various URL formats # TEST EDIT FOR CI/CD
def extract_video_id(url: str) -> str | None: 
    """Extracts YouTube video ID from various common link patterns."""
    try:
        parsed_url = urlparse(url)
        if parsed_url.hostname == "youtu.be":
            return parsed_url.path[1:]
        elif parsed_url.hostname in ["www.youtube.com", "youtube.com"]:
            if parsed_url.path == "/watch":
                query = parse_qs(parsed_url.query)
                return query.get("v", [None])[0] 
            elif parsed_url.path.startswith("/embed/"):
                return parsed_url.path.split("/")[2]
            elif parsed_url.path.startswith("/v/"):
                return parsed_url.path.split("/")[2]
        return None
    except Exception as e:

        logger.error(f"Error parsing URL '{url}': {e}", exc_info=True)
        return None

@app.get("/")
def root():
    """Returns a simple message indicating the service is running."""
    return {"message": "VidSynth Read Service Running"}

@app.post("/read", response_model=ReadOutput)
def read(request: ReadRequest):
    """
    Accepts a POST request containing a YouTube video link,
    extracts the video ID, and returns the ID along with the original link.
    """
    logger.info(f"READ: Received request for {request.video_link}")
    video_id = extract_video_id(request.video_link)

    if not video_id:
        logger.warning(f"Could not extract video_id from: {request.video_link}")
        raise HTTPException(status_code=400, detail="Invalid YouTube video link provided.")

    logger.info(f"READ: Extracted video_id: {video_id}")
    return ReadOutput(video_id=video_id, original_link=request.video_link)

