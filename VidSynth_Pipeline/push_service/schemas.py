from pydantic import BaseModel
from typing import List

# --- Input Schema ---
class PushInput(BaseModel):
    """
    Represents the data structure coming FROM the validate_service.
    Includes the video ID, full text, summaries, validation status, and issues.
    """
    video_id: str
    # video_summary: str
    comment_summary: str
    is_valid: bool
    issues: List[str]

# --- Output Schema ---
class PushOutput(BaseModel):
    """
    Represents the data structure returned BY the push_service.
    Indicates the final status ('pushed' or 'discarded') for the video ID.
    """
    status: str
    video_id: str

