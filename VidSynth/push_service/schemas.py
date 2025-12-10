from pydantic import BaseModel
from typing import List, Optional

# --- Bias Check Result Schema ---
class BiasCheckResult(BaseModel):
    """
    Represents the bias detection result from validate_service.
    """
    similarity_score: Optional[float] = None
    is_biased: bool
    threshold: float
    summary_preview: Optional[str] = None
    video_title: Optional[str] = None

# --- Input Schema ---
class PushInput(BaseModel):
    """
    Represents the data structure coming FROM the validate_service.
    """
    video_id: str
    video_summary: str
    comment_summary: str
    is_valid: bool
    issues: List[str]
    video_title: Optional[str] = None
    bias_check: Optional[BiasCheckResult] = None

# --- Output Schema ---
class PushOutput(BaseModel):
    """
    Represents the data structure returned BY the push_service.
    """
    status: str
    video_id: str