from fastapi import FastAPI
from pydantic import BaseModel
import requests

app = FastAPI()

class VideoRequest(BaseModel):
    video_id: str

@app.post("/summarize")
def summarize(request: VideoRequest):
    video_id = request.video_id

    # Step 1: Read transcript + comments
    read_res = requests.get(f"http://127.0.0.1:8001/read?video_id={video_id}").json()

    # Step 2: Preprocess
    preprocess_res = requests.post("http://127.0.0.1:8002/preprocess", json=read_res).json()

    # Step 3: LLM Summary
    llm_res = requests.post("http://127.0.0.1:8003/summarize", json=preprocess_res).json()

    # Step 4: Validation
    validate_res = requests.post("http://127.0.0.1:8004/validate", json=llm_res).json()

    return validate_res
