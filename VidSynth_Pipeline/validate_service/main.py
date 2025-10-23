# Import necessary libraries
from fastapi import FastAPI  
from schemas import LLMOutput, ValidateOutput 

# Initialize the FastAPI application instance
app = FastAPI(title="VidSynth Validate Service") 

@app.get("/")
def root():
    """Returns a simple message indicating the service is running."""
    return {"message": "VidSynth Validate Service Running"}

@app.post("/validate", response_model=ValidateOutput) 
def validate(request: LLMOutput):
    """
    Accepts a POST request with generated summaries (and full text),
    performs validation checks on the summaries, and returns the original data
    along with a validation status (is_valid flag and list of issues).
    """
    print("VALIDATE SERVICE: Validating summaries...")
    issues = []
    min_summary_length = 10 

    # --- Validation logic ---
    # Checks if the video summary is missing 
    if not request.video_summary or request.video_summary in ["No transcript available."]:
        issues.append("Video summary is missing or unavailable.")
    # If the summary exists and is not a placeholder, check its length (split into words)
    elif len(request.video_summary.split()) < min_summary_length:
        issues.append(f"Video summary is too short (less than {min_summary_length} words).")

    # Checks if the comment summary is missing 
    if not request.comment_summary or request.comment_summary in ["No comments available."]:
         issues.append("Comment summary is missing or unavailable.")
    # If it exists and is not a placeholder, check its length
    elif len(request.comment_summary.split()) < min_summary_length:
        issues.append(f"Comment summary is too short (less than {min_summary_length} words).")
    # --- End Validation ---

    is_valid = len(issues) == 0
    print(f"VALIDATE SERVICE: Validation complete. Valid: {is_valid}, Issues: {issues}")

    return ValidateOutput(
        video_id=request.video_id,  
        video_summary=request.video_summary,
        comment_summary=request.comment_summary,
        is_valid=is_valid,
        issues=issues
    )

