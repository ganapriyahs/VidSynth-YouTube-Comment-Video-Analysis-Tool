from pydantic import BaseModel
from typing import List

# --- Input Schema ---
class LLMOutput(BaseModel):
    """
    Represents the data structure coming FROM the llm_service.
    Includes the video ID and the generated summaries ONLY.
    """
    video_id: str
    # video_summary: str
    comment_summary: str

# --- Output Schema ---
class ValidateOutput(BaseModel):
    """
    Represents the data structure returned BY the validate_service.
    Includes the input summaries plus the validation status (is_valid flag)
    and a list of any issues found.
    """
    video_id: str
    # video_summary: str
    comment_summary: str
    is_valid: bool
    issues: List[str]

