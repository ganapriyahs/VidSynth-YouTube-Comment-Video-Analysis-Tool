from pydantic import BaseModel
from typing import List, Optional

# --- Bias Check Result Schema ---
class BiasCheckResult(BaseModel):
    similarity_score: Optional[float] = None
    is_biased: bool
    threshold: float
    summary_preview: Optional[str] = None
    video_title: Optional[str] = None

# --- Input Schema (From LLM) ---
class LLMOutput(BaseModel):
    video_id: str
    video_summary: str
    comment_summary: str
    video_title: Optional[str] = None 

# --- Output Schema (To Push) ---
class ValidateOutput(BaseModel):
    video_id: str
    video_summary: str
    comment_summary: str
    is_valid: bool
    issues: List[str]
    bias_check: Optional[BiasCheckResult] = None