from fastapi import FastAPI
import uvicorn

# Import your service methods (we will fix these paths after you confirm file names)
from read_service.main import extract_video_id
from preprocess_service.main import preprocess
from llm_service.main import generate_summary
from validate_service.main import validate_output

app = FastAPI()

@app.get("/summarize")
def summarize(videoId: str):

    # 1️⃣ Extract transcript & comments
    transcript, comments = extract_video_id(videoId)

    # 2️⃣ Preprocess
    cleaned = preprocess(transcript, comments)

    # 3️⃣ Generate summary
    result = generate_summary(cleaned)

    # 4️⃣ Validate
    final = validate_output(result)

    return {
        "video_summary": final.get("video_summary"),
        "comments_summary": final.get("comments_summary")
    }

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
