# For bias changes
from pydantic import BaseModel
from typing import List, Optional

# --- Input Schema ---
class LLMOutput(BaseModel):
    """
    Represents the data structure coming FROM the llm_service.
    """
    video_id: str
    video_summary: str
    comment_summary: str
    video_title: Optional[str] = None

# --- Bias Check Result Schema ---
class BiasCheckResult(BaseModel):
    """
    Represents the result of bias detection.
    """
    similarity_score: Optional[float] = None
    is_biased: bool
    threshold: float
    summary_preview: Optional[str] = None
    video_title: Optional[str] = None

# --- Output Schema ---
class ValidateOutput(BaseModel):
    """
    Represents the data structure returned BY the validate_service.
    """
    video_id: str
    video_summary: str
    comment_summary: str
    is_valid: bool
    issues: List[str]
    bias_check: Optional[BiasCheckResult] = None