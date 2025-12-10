#!/bin/bash
# =============================================================================
# LLM Service Setup Script
# Purpose: Download Llama model to GCS, push TGI to Artifact Registry,
#          deploy LLM service to Cloud Run with GPU
#
# Prerequisites:
#   - 01-bootstrap.sh has been run
#   - HuggingFace account with Llama license accepted
#   - HuggingFace token with read access
#
# Usage:
#   export HF_TOKEN="hf_your_token_here"
#   ./02-setup-llm.sh
#
# IMPORTANT: Run inside tmux to prevent Cloud Shell timeout:
#   tmux new -s llm-setup
#   ./02-setup-llm.sh
# =============================================================================

set -e

# =============================================================================
# CONFIGURATION
# =============================================================================
PROJECT_ID="vidsynth-demo-proj2025"
REGION="us-central1"
ZONE="us-central1-a"
ARTIFACT_REPO="vidsynth-repo"
BUCKET_NAME="vidsynth-demo-model-store"

# Model configuration
MODEL_ID="hugging-quants/Meta-Llama-3.1-8B-Instruct-AWQ-INT4"
MODEL_GCS_PATH="llama3-8b-awq"  # Will be gs://BUCKET_NAME/llama3-8b-awq/

# TGI configuration
TGI_SOURCE_IMAGE="ghcr.io/huggingface/text-generation-inference:2.4.1"
TGI_TARGET_IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/${ARTIFACT_REPO}/tgi:2.4.1"

# VM configuration (temporary, for setup only)
VM_NAME="llm-setup-vm"
VM_MACHINE_TYPE="e2-standard-4"  # 4 vCPU, 16GB RAM - no GPU needed for download
VM_DISK_SIZE="60GB"

# Cloud Run TGI service configuration
TGI_SERVICE_NAME="tgi-service"

# Registry base path
REGISTRY="${REGION}-docker.pkg.dev/${PROJECT_ID}/${ARTIFACT_REPO}"

# =============================================================================
# VALIDATE PREREQUISITES
# =============================================================================
log() {
    echo ""
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

log "Validating prerequisites..."

# Check HF_TOKEN
if [ -z "$HF_TOKEN" ]; then
    echo "ERROR: HF_TOKEN environment variable not set"
    echo ""
    echo "Get your token from: https://huggingface.co/settings/tokens"
    echo "Make sure you've accepted the Llama license at:"
    echo "  https://huggingface.co/meta-llama/Meta-Llama-3.1-8B-Instruct"
    echo ""
    echo "Then run:"
    echo "  export HF_TOKEN=\"hf_your_token_here\""
    echo "  ./02-setup-llm.sh"
    exit 1
fi

# Verify project
gcloud config set project "$PROJECT_ID"

# Check if bucket exists
if ! gcloud storage buckets describe "gs://${BUCKET_NAME}" &> /dev/null; then
    echo "ERROR: Bucket gs://${BUCKET_NAME} not found"
    echo "Run 01-bootstrap.sh first"
    exit 1
fi

# Check if artifact registry exists
if ! gcloud artifacts repositories describe "$ARTIFACT_REPO" --location="$REGION" &> /dev/null; then
    echo "ERROR: Artifact Registry ${ARTIFACT_REPO} not found"
    echo "Run 01-bootstrap.sh first"
    exit 1
fi

log "Prerequisites OK"

# =============================================================================
# CHECK IF ALREADY COMPLETED
# =============================================================================
log "Checking for existing resources..."

MODEL_EXISTS=false
TGI_EXISTS=false

# Check if model already in GCS
if gsutil ls "gs://${BUCKET_NAME}/${MODEL_GCS_PATH}/config.json" &> /dev/null; then
    log "Model already exists in GCS at gs://${BUCKET_NAME}/${MODEL_GCS_PATH}/"
    MODEL_EXISTS=true
fi

# Check if TGI already in Artifact Registry
if gcloud artifacts docker images describe "${TGI_TARGET_IMAGE}" &> /dev/null 2>&1; then
    log "TGI image already exists in Artifact Registry"
    TGI_EXISTS=true
fi

if [ "$MODEL_EXISTS" = true ] && [ "$TGI_EXISTS" = true ]; then
    log "Both model and TGI image already exist. Skipping to deployment."
else
    # =============================================================================
    # CREATE STARTUP SCRIPT FOR VM
    # =============================================================================
    log "Creating VM startup script..."

    STARTUP_SCRIPT=$(cat << 'STARTUP_EOF'
#!/bin/bash
set -ex

# Log everything
exec > /var/log/llm-setup.log 2>&1

echo "=== LLM Setup Script Started ==="
date

# Variables passed via metadata
PROJECT_ID=$(curl -s "http://metadata.google.internal/computeMetadata/v1/instance/attributes/project-id" -H "Metadata-Flavor: Google")
BUCKET_NAME=$(curl -s "http://metadata.google.internal/computeMetadata/v1/instance/attributes/bucket-name" -H "Metadata-Flavor: Google")
MODEL_GCS_PATH=$(curl -s "http://metadata.google.internal/computeMetadata/v1/instance/attributes/model-gcs-path" -H "Metadata-Flavor: Google")
MODEL_ID=$(curl -s "http://metadata.google.internal/computeMetadata/v1/instance/attributes/model-id" -H "Metadata-Flavor: Google")
HF_TOKEN=$(curl -s "http://metadata.google.internal/computeMetadata/v1/instance/attributes/hf-token" -H "Metadata-Flavor: Google")
TGI_SOURCE_IMAGE=$(curl -s "http://metadata.google.internal/computeMetadata/v1/instance/attributes/tgi-source-image" -H "Metadata-Flavor: Google")
TGI_TARGET_IMAGE=$(curl -s "http://metadata.google.internal/computeMetadata/v1/instance/attributes/tgi-target-image" -H "Metadata-Flavor: Google")
REGION=$(curl -s "http://metadata.google.internal/computeMetadata/v1/instance/attributes/region" -H "Metadata-Flavor: Google")
SKIP_MODEL=$(curl -s "http://metadata.google.internal/computeMetadata/v1/instance/attributes/skip-model" -H "Metadata-Flavor: Google")
SKIP_TGI=$(curl -s "http://metadata.google.internal/computeMetadata/v1/instance/attributes/skip-tgi" -H "Metadata-Flavor: Google")

echo "PROJECT_ID: $PROJECT_ID"
echo "BUCKET_NAME: $BUCKET_NAME"
echo "MODEL_GCS_PATH: $MODEL_GCS_PATH"
echo "MODEL_ID: $MODEL_ID"
echo "SKIP_MODEL: $SKIP_MODEL"
echo "SKIP_TGI: $SKIP_TGI"

# -----------------------------------------------------------------------------
# Install dependencies
# -----------------------------------------------------------------------------
echo "=== Installing dependencies ==="
apt-get update
apt-get install -y python3-pip docker.io

# Start Docker
systemctl start docker
systemctl enable docker

# Install huggingface-hub
pip3 install huggingface-hub

# -----------------------------------------------------------------------------
# Download and upload model (if not skipped)
# -----------------------------------------------------------------------------
if [ "$SKIP_MODEL" != "true" ]; then
    echo "=== Downloading model from HuggingFace ==="
    
    # Download model to /tmp/model (flat structure, no wrapper directory)
    python3 << PYTHON_EOF
from huggingface_hub import snapshot_download
import os

snapshot_download(
    repo_id="${MODEL_ID}",
    local_dir="/tmp/model",
    local_dir_use_symlinks=False,
    token="${HF_TOKEN}"
)
print("Download complete!")
PYTHON_EOF

    # Show what was downloaded
    echo "Downloaded files:"
    ls -lh /tmp/model/

    # Upload to GCS (contents only, not the directory itself)
    echo "=== Uploading model to GCS ==="
    gsutil -m cp -r /tmp/model/* "gs://${BUCKET_NAME}/${MODEL_GCS_PATH}/"

    # Verify upload
    echo "Uploaded files:"
    gsutil ls -lh "gs://${BUCKET_NAME}/${MODEL_GCS_PATH}/"

    echo "=== Model upload complete ==="
else
    echo "=== Skipping model download (already exists) ==="
fi

# -----------------------------------------------------------------------------
# Pull and push TGI image (if not skipped)
# -----------------------------------------------------------------------------
if [ "$SKIP_TGI" != "true" ]; then
    echo "=== Pulling TGI image ==="
    docker pull "$TGI_SOURCE_IMAGE"

    echo "=== Configuring Docker for Artifact Registry ==="
    gcloud auth configure-docker "${REGION}-docker.pkg.dev" --quiet

    echo "=== Tagging TGI image ==="
    docker tag "$TGI_SOURCE_IMAGE" "$TGI_TARGET_IMAGE"

    echo "=== Pushing TGI image to Artifact Registry ==="
    docker push "$TGI_TARGET_IMAGE"

    echo "=== TGI push complete ==="
else
    echo "=== Skipping TGI push (already exists) ==="
fi

# -----------------------------------------------------------------------------
# Signal completion
# -----------------------------------------------------------------------------
echo "=== Writing completion marker ==="
echo "completed at $(date)" | gsutil cp - "gs://${BUCKET_NAME}/.llm-setup-complete"

echo "=== LLM Setup Script Finished ==="
date
STARTUP_EOF
)

    # =============================================================================
    # CREATE AND RUN VM
    # =============================================================================
    log "Creating setup VM..."

    # Delete existing VM if present
    if gcloud compute instances describe "$VM_NAME" --zone="$ZONE" &> /dev/null; then
        log "Deleting existing VM..."
        gcloud compute instances delete "$VM_NAME" --zone="$ZONE" --quiet
    fi

    # Delete completion marker if exists
    gsutil rm "gs://${BUCKET_NAME}/.llm-setup-complete" 2>/dev/null || true

    # Create VM with startup script and metadata
    gcloud compute instances create "$VM_NAME" \
        --zone="$ZONE" \
        --machine-type="$VM_MACHINE_TYPE" \
        --boot-disk-size="$VM_DISK_SIZE" \
        --image-family=debian-11 \
        --image-project=debian-cloud \
        --scopes=cloud-platform \
        --metadata=\
project-id="$PROJECT_ID",\
bucket-name="$BUCKET_NAME",\
model-gcs-path="$MODEL_GCS_PATH",\
model-id="$MODEL_ID",\
hf-token="$HF_TOKEN",\
tgi-source-image="$TGI_SOURCE_IMAGE",\
tgi-target-image="$TGI_TARGET_IMAGE",\
region="$REGION",\
skip-model="$MODEL_EXISTS",\
skip-tgi="$TGI_EXISTS" \
        --metadata-from-file=startup-script=<(echo "$STARTUP_SCRIPT")

    log "VM created. Startup script is running..."
    log "This will take approximately 10-15 minutes."
    log ""
    log "You can monitor progress with:"
    log "  gcloud compute ssh $VM_NAME --zone=$ZONE --command='tail -f /var/log/llm-setup.log'"
    log ""

    # =============================================================================
    # WAIT FOR COMPLETION
    # =============================================================================
    log "Waiting for setup to complete..."

    TIMEOUT=1800  # 30 minutes
    ELAPSED=0
    INTERVAL=30

    while [ $ELAPSED -lt $TIMEOUT ]; do
        if gsutil ls "gs://${BUCKET_NAME}/.llm-setup-complete" &> /dev/null; then
            log "Setup completed!"
            break
        fi
        
        echo "  Still running... (${ELAPSED}s elapsed, checking again in ${INTERVAL}s)"
        sleep $INTERVAL
        ELAPSED=$((ELAPSED + INTERVAL))
    done

    if [ $ELAPSED -ge $TIMEOUT ]; then
        log "ERROR: Setup timed out after ${TIMEOUT}s"
        log "Check VM logs: gcloud compute ssh $VM_NAME --zone=$ZONE --command='cat /var/log/llm-setup.log'"
        exit 1
    fi

    # =============================================================================
    # CLEANUP VM
    # =============================================================================
    log "Deleting setup VM..."
    gcloud compute instances delete "$VM_NAME" --zone="$ZONE" --quiet
    log "VM deleted"

    # Clean up completion marker
    gsutil rm "gs://${BUCKET_NAME}/.llm-setup-complete" 2>/dev/null || true
fi

# =============================================================================
# DEPLOY LLM SERVICE TO CLOUD RUN
# =============================================================================
log "=========================================="
log "Deploying LLM Service to Cloud Run"
log "=========================================="

# Verify model exists
if ! gsutil ls "gs://${BUCKET_NAME}/${MODEL_GCS_PATH}/config.json" &> /dev/null; then
    log "ERROR: Model not found in GCS"
    exit 1
fi

# Verify TGI image exists
if ! gcloud artifacts docker images describe "${TGI_TARGET_IMAGE}" &> /dev/null 2>&1; then
    log "ERROR: TGI image not found in Artifact Registry"
    exit 1
fi

# Verify service.yaml exists
SERVICE_YAML="./tgi-service.yaml"
if [ ! -f "$SERVICE_YAML" ]; then
    log "ERROR: tgi-service.yaml not found in current directory"
    log "Make sure you run this script from the Deployment_Scripts/ directory"
    exit 1
fi

log "Deploying Cloud Run service with GPU using FUSE volume mount..."

# Deploy using service.yaml (creates or replaces)
gcloud run services replace "$SERVICE_YAML" --region="$REGION"

# Make TGI service publicly accessible
gcloud run services add-iam-policy-binding "$TGI_SERVICE_NAME" \
    --region="$REGION" \
    --member="allUsers" \
    --role="roles/run.invoker"

# Get service URL
TGI_URL=$(gcloud run services describe "$TGI_SERVICE_NAME" \
    --region="$REGION" --format="value(status.url)")

log "TGI service deployed: $TGI_URL"

# =============================================================================
# SUMMARY
# =============================================================================
log "=========================================="
log "TGI SETUP COMPLETE"
log "=========================================="

echo ""
echo "Model location:  gs://${BUCKET_NAME}/${MODEL_GCS_PATH}/"
echo "TGI image:       ${TGI_TARGET_IMAGE}"
echo "TGI service:     ${TGI_URL}"
echo ""
echo "Deployment uses GCS FUSE volume mount (no cold-start download required)."
echo "min-instances=1 keeps one instance warm to avoid cold starts."
echo ""
echo "Test the service:"
echo "  curl -X POST ${TGI_URL}/generate \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"inputs\": \"What is machine learning?\", \"parameters\": {\"max_new_tokens\": 100}}'"
echo ""
echo "Next step: Run ./03-deploy.sh to deploy other services and set Airflow variables"
