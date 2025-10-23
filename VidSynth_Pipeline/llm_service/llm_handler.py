# Import necessary libraries
import os  
import torch  
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM  
from google.cloud import storage  
import config  

class LLMHandler:
    def __init__(self):
        """
        Initializes the LLMHandler class. This involves:
        - Determining the compute device (CPU or GPU).
        - Detecting the environment (local or Cloud Run/GCP).
        - Loading the pre-trained tokenizer and model either from Hugging Face Hub
          or by downloading from Google Cloud Storage.
        """
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Initializing LLM on device: {self.device}")
        model_path_to_load = ""

        if "K_SERVICE" in os.environ:
            print("Cloud Run environment detected. Downloading model from GCS...")
            # Define the local path inside the container where the model will be saved
            local_model_path = "/tmp/model" 
            bucket_name = os.getenv("GCS_BUCKET_NAME")
            if bucket_name:
                print(f"Downloading model from bucket: {bucket_name} to {local_model_path}")
                self._download_model_from_gcs(bucket_name, local_model_path)
                model_path_to_load = local_model_path
            else:
                raise Exception("GCS_BUCKET_NAME environment variable not set in Cloud Run.")
        else:
            print("Local environment detected. Loading model from Hugging Face Hub.")
            model_path_to_load = config.MODEL_ID

        # --- Load Tokenizer and Model ---
        print(f"Loading model from: {model_path_to_load}")
        # Load the tokenizer associated with the pre-trained model
        self.tokenizer = AutoTokenizer.from_pretrained(model_path_to_load)
        print("Tokenizer loaded.")
        # Load the pre-trained sequence-to-sequence model
        # .to(self.device) moves the model to the selected device (CPU or GPU)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(model_path_to_load).to(self.device)
        print("Model loaded and moved to device.")
        print("LLM loaded successfully.")

    # Internal helper method to download model files from GCS
    def _download_model_from_gcs(self, bucket_name, destination_directory):
        """
        Downloads all files from a specified GCS bucket (and prefix)
        to a local directory inside the container.
        """
        # Ensure the local destination directory exists
        os.makedirs(destination_directory, exist_ok=True)
        # Initialize the Google Cloud Storage client
        storage_client = storage.Client()
        # Get a reference to the specified bucket
        bucket = storage_client.bucket(bucket_name)
        blobs = list(bucket.list_blobs(prefix="model/"))

        # Log the names of the files found in the bucket
        print(f"Found blobs: {[blob.name for blob in blobs]}")

        # Iterate through each blob found in the bucket
        for blob in blobs:
            relative_path = os.path.relpath(blob.name, "model/")
            destination_file_name = os.path.join(destination_directory, relative_path)
            parent_dir = os.path.dirname(destination_file_name)
            os.makedirs(parent_dir, exist_ok=True)

            # Log the download process for each file
            print(f"Downloading {blob.name} to {destination_file_name}...")
            # Download the blob's content to the specified local file
            blob.download_to_filename(destination_file_name)

        # Log completion of all downloads
        print("All blobs downloaded.")

    def generate_summary(self, prompt: str) -> str:
        """
        Takes a text prompt, tokenizes it, runs it through the loaded LLM model,
        and decodes the output to return a generated summary string.
        """
        # Log the beginning of the generation process, showing the start of the prompt
        print(f"Generating summary for prompt (first 100 chars): {prompt[:100]}...")
        inputs = self.tokenizer(prompt, return_tensors="pt", max_length=1024, truncation=True).to(self.device)

        outputs = self.model.generate(
            **inputs,
            min_length=50,  
            max_length=100,
            num_beams=4,   
            early_stopping=True 
        )

        summary = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        return summary

