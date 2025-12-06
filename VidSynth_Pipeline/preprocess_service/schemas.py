# For bias_changes
from pydantic import BaseModel
from typing import Optional

class VideoIdInput(BaseModel):
    """
    Represents the expected structure of the JSON payload
    sent TO the /preprocess endpoint.
    """
    video_id: str

class PreprocessOutput(BaseModel):
    """
    Represents the structure of the JSON payload
    sent FROM the /preprocess endpoint after fetching data.
    Now includes video_title for bias detection.
    """
    video_id: str
    transcript: str
    comments: str
    video_title: Optional[str] = None
