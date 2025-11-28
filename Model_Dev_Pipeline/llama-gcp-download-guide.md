# Downloading Llama 3.1 8B Model to Google Cloud Storage

## Prerequisites

1. **Google Cloud Account** with billing enabled
2. **HuggingFace Account**
   - Create account at https://huggingface.co
   - Go to https://huggingface.co/meta-llama/Meta-Llama-3.1-8B-Instruct
   - Click "Accept License" and wait for approval (usually instant)
   - Generate token at https://huggingface.co/settings/tokens (with "read" access)
3. **Google Cloud SDK** installed locally
   - Download from: https://cloud.google.com/sdk/docs/install#windows
   - Open "Google Cloud SDK Shell" after installation

## Step 1: Create Google Cloud Storage Bucket

In Google Cloud SDK Shell (PowerShell):

```powershell
# Authenticate with Google Cloud
gcloud auth login

# Set your project
gcloud config set project YOUR-PROJECT-ID

# Create bucket (name must be globally unique)
gsutil mb -l US gs://YOUR-PROJECT-ID-llm-models/

# Verify bucket was created
gsutil ls gs://YOUR-PROJECT-ID-llm-models/
```

## Step 2: Create Compute Engine VM for Download

Create a temporary VM with sufficient disk space:

```powershell
gcloud compute instances create model-downloader --machine-type=e2-standard-2 --boot-disk-size=50GB --zone=us-central1-a --image-family=debian-11 --image-project=debian-cloud
```

Wait for "Created" message, then connect:

```powershell
gcloud compute ssh model-downloader --zone=us-central1-a
```

Note: First SSH connection will create keys (press Enter when prompted)

## Step 3: Download Model Inside VM

Now you're in the Linux VM. Run these commands one at a time:

### Install required software:
```bash
# Update system
sudo apt-get update

# Install Python pip
sudo apt-get install python3-pip -y

# Install HuggingFace Hub
pip3 install --user huggingface-hub

# Add pip packages to PATH
export PATH=$PATH:~/.local/bin
```

### Authenticate with HuggingFace:
```bash
# Set your HuggingFace token
export HF_TOKEN="hf_your_token_here"
```

### Download the model:
```bash
# Create directory for model
mkdir llama-model

# Download Llama 3.1 8B (will take 10-20 minutes)
python3 -c "from huggingface_hub import snapshot_download; snapshot_download('meta-llama/Meta-Llama-3.1-8B-Instruct', local_dir='./llama-model', local_dir_use_symlinks=False, token='$HF_TOKEN')"
```

## Step 4: Clean Up Unnecessary Files

The download includes duplicate files in an "original" folder. Keep only what's needed:

```bash
# Save the important tokenizer.model file
cp llama-model/original/tokenizer.model llama-model/

# Remove the duplicate 15GB folder
rm -rf llama-model/original/

# Verify size is now ~15GB (not 30GB)
du -sh llama-model/
```

## Step 5: Upload to Google Cloud Storage

### Authenticate VM with Google Cloud:
```bash
# Login to Google Cloud from within VM
gcloud auth login
```
This will:
1. Display a URL - copy it
2. Paste URL in your browser
3. Login with your Google account
4. Copy the verification code
5. Paste code back in VM terminal

### Upload model to bucket:
```bash
# Upload model to your bucket (will take 2-5 minutes)
gsutil -m cp -r ./llama-model gs://YOUR-BUCKET-NAME/models/llama3-8b/

# Verify upload completed
gsutil ls -lh gs://YOUR-BUCKET-NAME/models/llama3-8b/
```

## Step 6: Clean Up VM

### Exit the VM:
```bash
exit
```

### Delete the VM (in PowerShell):
```powershell
gcloud compute instances delete model-downloader --zone=us-central1-a --quiet

# Verify VM is deleted
gcloud compute instances list
```

## Final Result

You should now have in your bucket at `gs://YOUR-BUCKET-NAME/models/llama3-8b/`:
- 4 model files: `model-00001-of-00004.safetensors` through `model-00004-of-00004.safetensors` (~15GB total)
- Configuration files: `config.json`, `generation_config.json`
- Tokenizer files: `tokenizer.json`, `tokenizer_config.json`, `tokenizer.model`
- Other metadata files

**Total size: ~15GB**  
**Total cost: ~$0.10** for VM time  
**Ongoing storage cost: ~$0.30/month**
