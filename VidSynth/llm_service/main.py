import logging
from fastapi import FastAPI, HTTPException
from schemas import PreprocessOutput, LLMOutput
from llm_handler import LLMHandler

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("uvicorn")

app = FastAPI(title="VidSynth LLM Service (Client)")

llm_engine = None

@app.on_event("startup")
async def startup_event():
    """Initialize the API Client."""
    global llm_engine
    try:
        llm_engine = LLMHandler()
        logger.info("✅ LLM Handler ready (connected to TGI backend)")
    except Exception as e:
        logger.error(f"CRITICAL: Failed to initialize LLM handler: {e}")

@app.get("/")
def root():
    status = "Ready" if llm_engine else "Not Ready"
    return {"message": f"VidSynth LLM Service (Client Mode). Status: {status}"}

@app.post("/run-llm", response_model=LLMOutput)
def run_llm(request: PreprocessOutput):
    if not llm_engine:
        raise HTTPException(status_code=503, detail="LLM Handler is not initialized.")

    logger.info(f"Processing video: {request.video_title}")

    # 1. Summarize Transcript (Video Summary)
    trans_prompt = (
        f"<|begin_of_text|><|start_header_id|>system<|end_header_id|> "
        f"You are a concise summarizer. Output only a single paragraph summarizing the video transcript, focusing on main topics and limiting the response to 100 words. DO NOT INCLUDE ANY INTRODUCTORY PHRASES OR LABELS.<|eot_id|>"
        f"<|start_header_id|>user<|end_header_id|>\n{request.transcript[:10000]}\n<|eot_id|>"
        f"<|start_header_id|>assistant<|end_header_id|>"
    )
    video_sum = llm_engine.generate(trans_prompt) 

    # 2. Summarize Comments (Comment Sentiment)
    comm_prompt = (
        f"<|begin_of_text|><|start_header_id|>system<|end_header_id|> "
        f"You are a concise sentiment analyst. Output only the summary of the overall sentiment and main discussion points in three short sentences. DO NOT INCLUDE ANY INTRODUCTORY PHRASES OR LABELS.<|eot_id|>"
        f"<|start_header_id|>user<|end_header_id|>\n{request.comments[:3000]}\n<|eot_id|>"
        f"<|start_header_id|>assistant<|end_header_id|>"
    )
    comment_sum = llm_engine.generate(comm_prompt)

    return LLMOutput(
        video_id=request.video_id,
        video_summary=video_sum,
        comment_summary=comment_sum,
        video_title=request.video_title
    )