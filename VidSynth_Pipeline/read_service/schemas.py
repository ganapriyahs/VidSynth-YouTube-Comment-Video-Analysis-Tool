from pydantic import BaseModel
from typing import Optional


class ReadRequest(BaseModel):
    """
    Represents the expected structure of the JSON payload
    sent TO the /read endpoint.
    """
    video_link: str

class ReadOutput(BaseModel):
    """
    Represents the structure of the JSON payload
    sent FROM the /read endpoint upon successful processing.
    """
    video_id: Optional[str] = None
    original_link: str

