import os
from dotenv import load_dotenv

load_dotenv()

# Set a fast, small default model for local testing
# MODEL_ID = os.getenv("MODEL_ID", "google/flan-t5-base")
MODEL_ID = os.getenv("MODEL_ID", "google/flan-t5-small")  # Change to small! for bias