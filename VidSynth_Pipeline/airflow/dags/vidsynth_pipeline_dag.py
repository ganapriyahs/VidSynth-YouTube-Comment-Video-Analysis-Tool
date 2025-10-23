# Import necessary libraries
import pendulum  
import requests 
from airflow.decorators import dag, task  
from airflow.models.param import Param  

# Define the URLs for each microservice.
# These use the Docker service names defined in docker-compose.yml,
# allowing Airflow tasks (running in Docker) to communicate with the services.
URL_READ = "http://read_service:5001/read" 
URL_PREPROCESS = "http://preprocess_service:5002/preprocess" 
URL_LLM = "http://llm_service:5003/run-llm" 
URL_VALIDATE = "http://validate_service:5004/validate"  
URL_PUSH = "http://push_service:5005/push"  

@dag(
    dag_id="vidsynth_pipeline",  
    start_date=pendulum.now("UTC"),  
    schedule=None,  
    catchup=False, 
    tags=["vidsynth", "mlops"],  

    # parameters added before triggering the dag
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
    """
    DAG to orchestrate the VidSynth microservices pipeline.
    This DAG requires a 'video_link' parameter in its configuration when triggered.
    It calls each microservice in sequence, passing data via Airflow XComs.
    """

    # Use the @task decorator to define the first task in the pipeline
    @task
    def read_service_task(**kwargs):
        """
        1. Calls the Read service.
        Accepts the YouTube link from the DAG's parameters, sends it to the
        read_service, and returns the service's response (containing the video_id).
        """
        params = kwargs.get('params', {})
        video_link = params.get("video_link")
        if not video_link:
            raise ValueError("No 'video_link' provided in DAG config JSON.")
        print(f"READ: Sending request for {video_link}")
        # Make a POST request to the read_service URL with the video link in JSON format
        response = requests.post(URL_READ, json={"video_link": video_link})
        response.raise_for_status()
        return response.json()

    # Define the second task, accepting the output (XCom) from the previous task
    @task
    def preprocess_service_task(read_data: dict):
        """
        2. Calls the Preprocess service.
        Accepts the dictionary returned by read_service_task (containing video_id),
        sends it to the preprocess_service, and returns the response (transcript and comments).
        """
        video_id = read_data.get("video_id")
        if not video_id:
            raise ValueError("Read service did not return a video_id.")

        # Log the action
        print(f"PREPROCESS: Fetching data for video_id: {video_id}")
        response = requests.post(URL_PREPROCESS, json=read_data)
        response.raise_for_status()
        return response.json()

    # Define the third task
    @task
    def llm_service_task(preprocess_data: dict):
        """
        3. Calls the LLM service.
        Accepts the dictionary from preprocess_service_task (transcript and comments),
        sends it to the llm_service for summarization, and returns the response (summaries).
        """
        # Log the action
        print("LLM: Generating summaries...")
        response = requests.post(URL_LLM, json=preprocess_data)
        response.raise_for_status()
        return response.json()

    # Define the fourth task
    @task
    def validate_service_task(llm_data: dict):
        """
        4. Calls the Validate service.
        Accepts the dictionary from llm_service_task (summaries), sends it to the
        validate_service for quality checks, and returns the response (validation status).
        """
        # Log the action
        print("VALIDATE: Checking summary content...")
        response = requests.post(URL_VALIDATE, json=llm_data)
        response.raise_for_status()
        return response.json()

    # Define the fifth 
    @task
    def push_service_task(validate_data: dict):
        """
        5. Calls the Push service.
        Accepts the dictionary from validate_service_task (validation status and summaries),
        sends it to the push_service for final processing (e.g., logging or saving to DB).
        Returns the final status response.
        """
        if not validate_data.get("is_valid"):
            # If the data is invalid, log it and return a 'discarded' status
            # This task run will still be marked as 'success' in Airflow, but indicates the data wasn't pushed
            print(f"PUSH: Job is invalid, discarding. Issues: {validate_data.get('issues')}")
            # Return a dictionary indicating the outcome (will be stored as XCom but likely not used)
            return {"status": "discarded", "video_id": validate_data.get("video_id"), "reason": validate_data.get("issues")}

        # Log the action if the data is valid
        print("PUSH: Finalizing results...")
        response = requests.post(URL_PUSH, json=validate_data)
        response.raise_for_status()
        # Log completion
        print("PUSH complete.")
        return response.json()

    # Define the pipeline dependencies using the TaskFlow API
    # This sets the execution order and handles passing XComs between tasks.
    read_output = read_service_task() 
    preprocess_output = preprocess_service_task(read_output)  
    llm_output = llm_service_task(preprocess_output)  
    validate_output = validate_service_task(llm_output) 
    push_service_task(validate_output) 

# Instantiate the DAG object, making it visible to Airflow
vidsynth_processing_pipeline()

