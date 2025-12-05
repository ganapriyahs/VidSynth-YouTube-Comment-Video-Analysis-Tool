from pydantic import BaseModel

class VideoIdInput(BaseModel):
    """
    Represents the expected structure of the JSON payload
    sent TO the /preprocess endpoint. It requires a YouTube video ID.
    """
    video_id: str

class PreprocessOutput(BaseModel):
    """
    Represents the structure of the JSON payload
    sent FROM the /preprocess endpoint after fetching data.
    """
    video_id: str
    # transcript: str
    comments: str

