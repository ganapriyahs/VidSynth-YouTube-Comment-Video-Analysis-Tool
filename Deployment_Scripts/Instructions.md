# GCP Bootstrap & Deployment Scripts

Automates GCP project setup and Cloud Run deployment for the VidSynth pipeline.

## Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     PHASE 1: Bootstrap                          │
│                   (Run once, ~5 min)                            │
│                                                                 │
│   01-bootstrap.sh                                               │
│   ├── Create GCP project                                        │
│   ├── Link billing account                                      │
│   ├── Enable APIs (Artifact Registry, Cloud Run, etc.)          │
│   ├── Create Artifact Registry repo                             │
│   ├── Create model storage bucket                               │
│   └── Create results storage bucket                             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    PHASE 2: TGI Setup                           │
│              (Run inside tmux, ~20 min total)                   │
│                                                                 │
│   02-setup-llm.sh                                               │
│   ├── 1. Create temp VM for setup                               │
│   ├── 2. Download Llama model from HuggingFace → GCS            │
│   ├── 3. Pull TGI image → push to Artifact Registry             │
│   ├── 4. Deploy TGI service to Cloud Run with GPU               │
│   └── 5. Delete temp VM                                         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    PHASE 3: Deployment                          │
│              (Run inside tmux, ~30 min total)                   │
│                                                                 │
│   03-deploy.sh                                                  │
│   ├── 1. Start Composer creation (async)                        │
│   ├── 2. Build & deploy Cloud Run services (~10 min)            │
│   │      (read, preprocess, validate, push, llm-wrapper)        │
│   ├── 3. Wait for Composer to be ready (~25 min from start)     │
│   ├── 4. Set Airflow Variables (all service URLs)               │
│   ├── 5. Upload DAG                                             │
│   └── 6. Deploy gateway service                                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      PHASE 4: Teardown                          │
│                  (When demo is complete)                        │
│                                                                 │
│   99-teardown.sh                                                │
│   ├── Option 1: Delete entire project (30-day ID lockout)       │
│   └── Option 2: Delete resources only (reuse project ID)        │
└─────────────────────────────────────────────────────────────────┘
```

## Directory Structure

These scripts assume the following repo structure:

```
vidsynth/  (repo root)
├── Deployment_Scripts/
│   ├── 01-bootstrap.sh
│   ├── 02-setup-llm.sh
│   ├── 03-deploy.sh
│   ├── 99-teardown.sh
│   └── tgi-service.yaml
└── VidSynth/
    ├── read_service/
    ├── preprocess_service/
    ├── llm_service/          # Wrapper that calls TGI
    ├── validate_service/
    ├── push_service/
    ├── gateway_service/      # Frontend API
    └── airflow/
        └── dags/
            └── vidsynth_pipeline_dag.py
```

## Prerequisites

1. **gcloud CLI** installed: https://cloud.google.com/sdk/docs/install
2. **Authenticated**: Run `gcloud auth login`
3. **Billing Account ID**: Find via `gcloud billing accounts list`

## Quick Start (Cloud Shell recommended)

```bash
# Clone your repo
git clone https://github.com/YOUR_USERNAME/vidsynth.git
cd vidsynth/Deployment_Scripts

# Make scripts executable
chmod +x *.sh

# 1. Run bootstrap (~5 min)
export BILLING_ACCOUNT="01XXXX-XXXXXX-XXXXXX"
./01-bootstrap.sh

# 2. Start tmux session (prevents Cloud Shell timeout)
tmux new -s deploy

# 3. Run TGI setup (~20 min) - requires HuggingFace token
export HF_TOKEN="hf_your_token_here"
./02-setup-llm.sh

# 4. Run deployment (~30 min total) - requires YouTube API key
export YOUTUBE_API_KEY="your-youtube-api-key"
./03-deploy.sh

# If Cloud Shell disconnects, reconnect and run:
#   tmux attach -t deploy

# 5. When demo is complete, tear down
./99-teardown.sh
```

## LLM Setup Prerequisites

Before running `02-setup-llm.sh`:

1. **Create HuggingFace account**: https://huggingface.co
2. **Accept Llama license**: https://huggingface.co/meta-llama/Meta-Llama-3.1-8B-Instruct
3. **Generate token**: https://huggingface.co/settings/tokens (read access)

The script downloads the quantized AWQ version (~4GB instead of ~16GB) for faster setup.

## Deployment Prerequisites

Before running `03-deploy.sh`:

1. **YouTube Data API key**: https://console.cloud.google.com/apis/credentials
   - Create a new API key or use existing one
   - Enable YouTube Data API v3 for your project

**Note:** Running `02-setup-llm.sh` before `03-deploy.sh` ensures the LLM URL is automatically set as an Airflow variable.

## Tmux Information

Cloud Shell times out after ~20 minutes of idle time. The deployment script takes ~30 minutes (mostly waiting for Composer). Tmux creates a persistent session that keeps running even if your browser disconnects:

```bash
tmux new -s deploy      # Start new session named "deploy"
./03-deploy.sh          # Run script inside tmux

# If disconnected, reconnect to Cloud Shell then:
tmux attach -t deploy   # Reattach to see progress

# When done:
tmux kill-session -t deploy   # Clean up session
```


## DAG Configuration

The DAG must read Cloud Run URLs from Airflow Variables (set automatically by `03-deploy.sh`). Update your DAG to use:

```python
from airflow.models import Variable

# Read URLs from Airflow Variables (set by 03-deploy.sh)
URL_READ = Variable.get("URL_READ")
URL_PREPROCESS = Variable.get("URL_PREPROCESS")
URL_VALIDATE = Variable.get("URL_VALIDATE")
URL_PUSH = Variable.get("URL_PUSH")
URL_LLM = Variable.get("URL_LLM")
```

All variables are set automatically by `03-deploy.sh` (including `URL_LLM` if you ran `02-setup-llm.sh` first).

