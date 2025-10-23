#### Architecture
architecture orchestrated by Apache Airflow:

#### FastAPI Microservices (Python):
read_service: Receives a full YouTube video URL, extracts the Video ID.
preprocess_service: Receives the Video ID, fetches the video transcript and top comments using the YouTube Transcript API and YouTube Data API v3.
llm_service: Receives the transcript and comments, uses a Hugging Face Transformer model (e.g., Flan-T5) to generate summaries for both.
validate_service: Performs basic quality checks on the generated summaries (e.g., length, checks for placeholders).
push_service: Receives the validated summaries and logs them (in a real application, this would save to a database or send to a front-end).

#### Apache Airflow (Orchestration):
Manages the workflow, calling each microservice in the correct sequence.
Uses the CeleryExecutor for potentially distributing tasks (though running locally in this setup).
Provides a Web UI for triggering pipelines, monitoring runs, and viewing logs.

#### Docker & Docker Compose:
Each microservice and Airflow component runs in its own isolated Docker container.
docker-compose.yml defines and links all the services (FastAPI services, Airflow Webserver/Scheduler/Worker, Redis, Postgres).

#### Redis: 
Acts as the message broker for the Airflow CeleryExecutor.

#### PostgreSQL: 
Serves as the metadata database for Airflow.

#### Prerequisites
Docker Desktop: Ensure Docker Desktop (or Docker Engine + Docker Compose) is installed and running on your system. Download from Docker's website.

#### Setup

1. Clone the Repository:

git clone [https://github.com/ganapriyahs/VidSynth-YouTube-Comment-Video-Analysis-Tool.git](https://github.com/ganapriyahs/VidSynth-YouTube-Comment-Video-Analysis-Tool.git)
cd "VidSynth-YouTube-Comment-Video-Analysis-Tool/VidSynth_Pipeline"


2. Configure YouTube API Key:
You need a YouTube Data API v3 Key to fetch comments.
Go to the Google Cloud Console.
Create a new project (or select an existing one).
Enable the "YouTube Data API v3" for your project.
Go to "Credentials" and create an "API key". Restrict this key if deploying publicly (e.g., restrict by IP address).
Open the file preprocess_service/.env.
Paste your API key into the file:
YOUTUBE_API_KEY=YOUR_API_KEY_HERE


3. Running the Application

Build and Start Services:
Open your terminal in the root directory of the project (VidSynth-YouTube-Comment-Video-Analysis-Tool/VidSynth_Pipeline).

Run the following command. This will build the Docker images for all services and start them in the background (-d).
docker compose up --build -d

Wait: The first time you run this, it might take several minutes to download images, build containers, and initialize Airflow (including database migration and user creation). Wait 2-3 minutes for everything to become healthy. You can check the status using "docker compose ps"

4. If the localhost is still not responding, run this command, docker compose exec airflow-webserver bash -c "airflow db migrate"

5. Using the Application
Access Airflow UI:
Open your web browser and go to: http://localhost:8080

6. Login:
Use the credentials defined in the root .env file (default):
Username: airflow
Password: airflow

7. Trigger the Pipeline:
On the Airflow homepage (DAGs view), find the vidsynth_pipeline.
Unpause the DAG using the toggle switch on the left if it's paused.
Click the Play (▶) button on the right side.
A configuration pop-up box will appear.
Paste the full YouTube video URL you want to process into the video_link field. Make sure it's a video that has transcripts/captions available.
{
  "video_link": "[https://www.youtube.com/watch?v=YOUR_VIDEO_ID_HERE](https://www.youtube.com/watch?v=YOUR_VIDEO_ID_HERE)"
}

Click the "Trigger" button.

8. Monitor and View Results:
Click on the vidsynth_pipeline name to go to the Grid view.
You can see the tasks (read_service_task, preprocess_service_task, etc.) run and change color (queued -> running -> success/failed).
Once the final push_service_task shows Success (green), click on that task instance box.
A pop-up will appear. Click the "Log" tab.
Scroll down in the logs. You will find the final generated Video Summary and Comment Summary logged by the push_service.
Stopping the Application

9. To stop all running containers associated with this project, open your terminal in the project root directory and run:
docker compose down

