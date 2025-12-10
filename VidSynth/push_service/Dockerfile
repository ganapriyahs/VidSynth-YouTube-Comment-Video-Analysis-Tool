FROM python:3.10-slim
WORKDIR /app

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port 8080 (Required for Cloud Run)
EXPOSE 8080

# Start Uvicorn directly (Correct for FastAPI)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]