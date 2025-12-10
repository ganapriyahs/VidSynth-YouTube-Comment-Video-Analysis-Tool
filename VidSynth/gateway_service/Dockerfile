FROM python:3.10-slim
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Expose the port Cloud Run expects
EXPOSE 8080

# Start the application with Gunicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]