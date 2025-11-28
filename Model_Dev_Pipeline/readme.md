# Model Development Pipeline  

### General Overview:  
Currently, the code is seperate and standalone from our overall Data Pipeline. These validation steps will indicate if the open-source model chosen will meet the requirments of our product; The quality of YouTube video and comment section summaries will be evaluated based on factual correctness, brevity, and overall abstractive quality. The validation is primarily performed via LLM as a judge.  

### Code Structure 
Within the /src folder there are 3 python scripts to perform one full pass of validation on the test set. These files are "initialize_validation_set.py", "generate_summaries_all_test.py", and "validate_summaries.py". The 'videos.txt' file is the list of YouTube urls that will be used for validation. The 'videoList.json' is the output after validation test and contains many meta data fields. The two remaining python files 'YouTubeTranPull.py' and 'YouTubeCommentPull.py" simply contain helper functions that are used by the other 3 files. 


### Preliminary Setup  
This code requires 3 API keys to run:   
 1. YouTube Data API
    - see main Readme for creation 
 2. Hugging Face API
 3.  OpenAI API
  
 **Hugging Face API:**  
 Since, this code is currently seperate from the main data pipeline, it does not have access to our hosted open source LLM on GCP. Therefore, the HuggingFace API is used so that LLM inference and the remainder of this code can be run locally.  
 **Setup:** 
 Unusually, it requires two steps. Since we are currently using Llama 3.1-8B, the first step requires to obtain permission to use this model by submitting a form.  
 
 The form can be found on the model page: [Link](https://huggingface.co/meta-llama/Llama-3.1-8B-Instruct)  
 Approval should take less than 30 minutes. Status of approval can be viewed within your user settings: [Link](https://huggingface.co/settings/gated-repos)  
 After you see that the request is approved, you must then create a Hugging Face API token. The link is at: [Link](https://huggingface.co/settings/tokens)  
  
You should select fine-grained: select all read access options, leave alone the write options, but make sure you select the repo options and add the Llamma repo that you were just approved for.  
**Note: You will not need to setup billing, this service is completely free**  

**OpenAI key**
On the other hand, this service requires billing. However, for testing purposes it should cost less than 50 cents. *However, there may be an option to get sufficient free usage if you choose to share API data with OpenAI*  
[Home Page For OpenAI API](https://platform.openai.com/docs/overview)  
To create an API key, naviaget to the following link: [API KEY page](https://platform.openai.com/settings/organization/api-keys)  

### Code setup (Docker):
1. ```cd Model_Dev_Pipeline```
2. ```docker build -t model-dev-pipeline```
3. ```docker run model-dev-pipeline``` 

### Code setup (Manual):  
1. Create a virtual environment
2. ```pip install -r requirements.txt```
3. Change directory to 'Src' folder  
4. Add your API keys to .env file
5. ```python initialize_validation_set.py```
6. ```python generate_summaries_all_test.py```
7. ```python validate_summaries.py```

At this point, you should have a new file named 'videoList.json'. This file contains each trial (each video): 
**Meta Data:** 
- Video url
- The speker's demographic (example: Chinese, or English language)
- video genre 
- video duration  

**Raw/Source data**
- transcript data 
- transcript summary
- comment data
- comment summary

**Validation data**  
- validation score for both transcript, and comment section summary, range: [0,1]
- LLM reasoning for giving score for both also. 
 