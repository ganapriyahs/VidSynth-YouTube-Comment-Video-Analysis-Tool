from pydantic import BaseModel

# --- Input Schema ---
class PreprocessOutput(BaseModel):
    """
    Represents the data structure coming from the preprocess service.
    Contains the raw text data needed for summarization.
    """
    video_id: str
    # transcript: str
    comments: str

# --- Output Schema ---
class LLMOutput(BaseModel):
    """
    Represents the data structure returned by the LLM service.
    Contains the video ID and the generated summaries ONLY.
    """
    video_id: str
    # video_summary: str
    comment_summary: str

