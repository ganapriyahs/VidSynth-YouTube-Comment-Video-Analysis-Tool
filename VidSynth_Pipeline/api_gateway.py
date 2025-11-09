from fastapi import FastAPI
import requests

app = FastAPI()

@app.get("/summarize")
def summarize(video_id: str):
    try:
        # 1️⃣ READ SERVICE: extract transcript & comments
        transcript = requests.get(f"http://localhost:8001/read?video_id={video_id}").json()

        # 2️⃣ PREPROCESS SERVICE
        processed = requests.post("http://localhost:8002/preprocess", json=transcript).json()

        # 3️⃣ LLM SERVICE: generate summary
        summary = requests.post("http://localhost:8003/summarize", json=processed).json()

        # 4️⃣ VALIDATION SERVICE
        validated = requests.post("http://localhost:8004/validate", json=summary).json()

        return validated
    
    except Exception as e:
        return {"error": str(e), "message": "Backend services not running"}
