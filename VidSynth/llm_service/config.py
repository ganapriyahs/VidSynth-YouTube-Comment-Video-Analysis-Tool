import os
from dotenv import load_dotenv

load_dotenv()

MODEL_ID = "meta-llama/Llama-3.1-8B-Instruct"

GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME")