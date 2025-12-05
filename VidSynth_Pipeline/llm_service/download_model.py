# download_model.py
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import os

# 1. Define the model name 
# Note: 'flan-t5-large' is ~3GB. Make sure your internet is stable!
model_name = "google/flan-t5-large" 

# 2. CORRECTED: Save to a subfolder, not the root code folder
output_dir = "./model_dump" 

print(f"Downloading {model_name} from Hugging Face...")

# 3. Load and Save Tokenizer
tokenizer = AutoTokenizer.from_pretrained(model_name)
tokenizer.save_pretrained(output_dir)

# 4. Load and Save Model
model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
model.save_pretrained(output_dir)

print(f"Success! Model saved to: {os.path.abspath(output_dir)}")