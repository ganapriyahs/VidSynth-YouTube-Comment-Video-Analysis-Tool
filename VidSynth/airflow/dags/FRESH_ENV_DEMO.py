import pendulum
import requests
from airflow.decorators import dag, task
from airflow.models.param import Param
from airflow.models import Variable 

# NOTE: Old Hardcoded method (without automation)
# =====================================================================
# Define the URLs for each microservice.
# These use the Docker service names defined in docker-compose.yml,
# allowing Airflow tasks (running in Docker) to communicate with the services.
# URL_READ = "http://read_service:5001/read" 
# URL_PREPROCESS = "http://preprocess_service:5002/preprocess" 
# URL_LLM = "http://llm_service:5003/run-llm" 
# URL_VALIDATE = "http://validate_service:5004/validate"  
# URL_PUSH = "http://push_service:5005/push"  
# ======================================================================

# URLS grabbed from 02-deploy.sh script
URL_READ = Variable.get("URL_READ")
URL_PREPROCESS = Variable.get("URL_PREPROCESS")
URL_LLM = Variable.get("URL_LLM")
URL_VALIDATE = Variable.get("URL_VALIDATE")
URL_PUSH = Variable.get("URL_PUSH")

@dag(
    dag_id="vidsynth_pipeline",
    start_date=pendulum.datetime(2024, 1, 1, tz="EST"),
    schedule=None,
    catchup=False,
    max_active_runs=3,
    tags=["vidsynth", "monolithic"],
    params={
        "video_link": Param(
            "https://www.youtube.com/watch?v=HAnw168huqA",
            type="string",
            title="YouTube Video Link",
            description="Paste the full YouTube URL to summarize.",
        )
    },
)
def vidsynth_processing_pipeline():

    @task
    def read_service_task(**kwargs):
        dag_run = kwargs.get('dag_run')
        video_link = None
        if dag_run and dag_run.conf:
            video_link = dag_run.conf.get('video_link')
        
        if not video_link:
            video_link = kwargs['params']['video_link']

        print(f"READ: Sending request for {video_link}")
        try:
            response = requests.post(URL_READ, json={"video_link": video_link}, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"READ FAILED: {e}")
            raise

    @task
    def preprocess_service_task(read_data: dict):
        video_id = read_data.get("video_id")
        print(f"PREPROCESS: Fetching data for {video_id}")
        
        try:
            response = requests.post(URL_PREPROCESS, json=read_data, timeout=60)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"PREPROCESS FAILED: {e}")
            raise

    @task
    def llm_service_task(preprocess_data: dict):
        print(f"LLM: Sending data to Monolithic Llama 3 Service...")
        
        try:
            response = requests.post(URL_LLM, json=preprocess_data, timeout=600)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"LLM FAILED: {e}")
            raise

    @task
    def validate_service_task(llm_data: dict):
        print("VALIDATE: Checking for bias and quality...")
        try:
            response = requests.post(URL_VALIDATE, json=llm_data, timeout=300)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"VALIDATE FAILED: {e}")
            raise

    @task
    def push_service_task(validate_data: dict):
        if not validate_data.get("is_valid"):
            print(f"PUSH ABORTED: Job is invalid. Issues: {validate_data.get('issues')}")
            return {
                "status": "discarded",
                "video_id": validate_data.get("video_id"),
                "reason": validate_data.get("issues")
            }

        print("PUSH: Finalizing results...")
        try:
            response = requests.post(URL_PUSH, json=validate_data, timeout=30)
            response.raise_for_status()
            print("PUSH SUCCESS.")
            return response.json()
        except Exception as e:
            print(f"PUSH FAILED: {e}")
            raise

    # --- DEFINE WORKFLOW ---
    read_output = read_service_task()
    preprocess_output = preprocess_service_task(read_output)
    llm_output = llm_service_task(preprocess_output)
    validate_output = validate_service_task(llm_output)
    push_service_task(validate_output)

# Instantiate
vidsynth_processing_pipeline()