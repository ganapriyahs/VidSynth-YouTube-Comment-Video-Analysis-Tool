# Import necessary libraries
from fastapi import FastAPI, HTTPException  
from schemas import PreprocessOutput, LLMOutput  
from llm_handler import LLMHandler  

# FastAPI application instance
app = FastAPI(title="VidSynth LLM Service") 
llm_handler = None

@app.on_event("startup")
def startup_event():
    """
    Loads the LLM model when the service starts up.
    This is preferred over loading it on the first request to avoid cold starts
    and to handle potential loading errors early.
    """
    global llm_handler
    print("LLM SERVICE: Application startup... loading model.")
    try:
        llm_handler = LLMHandler()
        print("LLM SERVICE: Model loaded successfully.")
    except Exception as e:
        print(f"LLM SERVICE: CRITICAL - Model failed to load: {e}")
        llm_handler = None
 
@app.get("/")
def root():
    """Returns a simple message indicating the service is running."""
    return {"message": "VidSynth LLM Service Running"}

# Define the main POST endpoint "/run-llm"
# It expects data matching the PreprocessOutput schema and returns data matching the LLMOutput schema
@app.post("/run-llm", response_model=LLMOutput) # Use updated output model (only summaries)
def run_llm(request: PreprocessOutput): # Expects full transcript and comments from the preprocess service
    """
    Accepts a POST request with transcript and comments, generates summaries
    using prompts similar to the working monolithic code, and returns only the summaries.
    """
    print("LLM SERVICE: Received request to generate summaries.")
    if not llm_handler:
        print("LLM SERVICE: Model not loaded, returning 503.")
        raise HTTPException(status_code=503, detail="Model is not loaded or failed to load.")

    # video_prompt = f"Summarize the key points of the following video transcript:\n\n{request.transcript}"
    comment_prompt = f"Summarize the overall sentiment and main themes from these user comments:\n\n{request.comments}"

    # print("LLM SERVICE: Generating video summary...")
    # Generate the video summary using the llm_handler instance
    # video_summary = llm_handler.generate_summary(video_prompt) if request.transcript else "No transcript available."
    print("LLM SERVICE: Generating comment summary...")
    # Generate the comment summary using the llm_handler instance
    comment_summary = llm_handler.generate_summary(comment_prompt) if request.comments else "No comments available."
    print("LLM SERVICE: Summaries generated.")

    return LLMOutput(
        video_id=request.video_id,
        # video_summary=video_summary,
        comment_summary=comment_summary
    )

