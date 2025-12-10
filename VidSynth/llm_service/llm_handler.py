import logging
import requests
import json

logger = logging.getLogger("uvicorn")

class LLMHandler:
    def __init__(self):
        logger.info("🚀 Initializing TGI LLM Client...")
        self.api_url = "YOUR_TGI_CLOUD_RUN_URL"
        
        logger.info(f"🔗 Configured to use TGI Service at: {self.api_url}")

    def generate(self, prompt: str) -> str:
        """
        Sends the prompt to the TGI service and returns the generated text.
        """
        headers = {
            "Content-Type": "application/json"
        }
        
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": 512, 
                "temperature": 0.3,
                "do_sample": True,
            }
        }

        try:
            response = requests.post(self.api_url, json=payload, headers=headers, timeout=120)
            response.raise_for_status()
            
            result = response.json()
            
            if isinstance(result, list) and "generated_text" in result[0]:
                generated_text = result[0]["generated_text"]
                if generated_text.startswith(prompt):
                    return generated_text[len(prompt):].strip()
                return generated_text.strip()
            
            return result.get("generated_text", "")

        except requests.exceptions.RequestException as e:
            logger.error(f"Error calling TGI Service: {e}")
            return f"Error generating content: {str(e)}"