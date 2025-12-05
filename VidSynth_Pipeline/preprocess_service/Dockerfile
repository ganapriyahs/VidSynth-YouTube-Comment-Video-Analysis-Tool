FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip youtube-transcript-api

RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 5002
CMD ["gunicorn", "-w", "2", "-k", "uvicorn.workers.UvicornWorker", "main:app", "--bind", "0.0.0.0:8080"]

