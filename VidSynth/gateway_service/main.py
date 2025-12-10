import json
import logging
import requests
import google.auth
from google.auth.transport.requests import Request
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google.cloud import storage

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="VidSynth Gateway")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- CONFIGURATION ---
# PROJECT_ID = "vidsynth" # seemingly unused 
RESULTS_BUCKET = "vidsynth-results" # can keep hard coded, since will have been already created before deploy 
DAG_ID = "vidsynth_pipeline" # simlar to above 

# AIRFLOW_WEBSERVER_URL = "YOUR_AIRFLOW_WEBSERVER_URL"  # MAYBE put back for CI/CD continous deploy, GitHub secret?
AIRFLOW_WEBSERVER_URL = os.getenv("AIRFLOW_WEBSERVER_URL")

class VideoRequest(BaseModel):
    video_id: str

@app.get("/")
def root():
    return {"message": "VidSynth Gateway is Running (Fast Mode)"}

@app.post("/summarize")
def trigger_pipeline(request: VideoRequest):
    video_id = request.video_id
    video_link = f"https://www.youtube.com/watch?v={video_id}"
    logger.info(f"Triggering DAG for: {video_link}")

    
    if not AIRFLOW_WEBSERVER_URL:
        raise HTTPException(status_code=500, detail="AIRFLOW_WEBSERVER_URL not configured")

    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(RESULTS_BUCKET)
        blob = bucket.blob(f"{video_id}.json")
        if blob.exists():
            logger.info("Deleting stale data...")
            blob.delete()

        credentials, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
        credentials.refresh(Request())
        access_token = credentials.token

        endpoint = f"{AIRFLOW_WEBSERVER_URL}/api/v1/dags/{DAG_ID}/dagRuns"
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        

        payload = {
            "conf": {"video_link": video_link}
        }


        logger.info(f"Hitting Airflow API: {endpoint}")
        response = requests.post(endpoint, json=payload, headers=headers)
        
        if response.status_code != 200:
            logger.error(f"Airflow API Error: {response.text}")
            raise HTTPException(status_code=500, detail=f"Airflow refused trigger: {response.text}")

        return {
            "status": "started", 
            "message": "Pipeline triggered instantly via REST API",
            "video_id": video_id
        }

    except Exception as e:
        logger.error(f"Gateway Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/result/{video_id}")
def get_result(video_id: str):
    try:
        client = storage.Client()
        bucket = client.bucket(RESULTS_BUCKET)
        blob = bucket.blob(f"{video_id}.json")

        if blob.exists():
            content = blob.download_as_text()
            data = json.loads(content)
            return data 
        else:
            return {"status": "processing"}
            
    except Exception as e:
        logger.error(f"Error checking result: {e}")
        raise HTTPException(status_code=500, detail=str(e))