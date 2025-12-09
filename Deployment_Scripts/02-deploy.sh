#!/bin/bash
# =============================================================================
# Full Deployment Script
# Purpose: Deploy Cloud Composer, Cloud Run services, set Airflow variables,
#          and upload DAG — all in one sequential script
# 
# IMPORTANT: Run this inside tmux to prevent Cloud Shell timeout issues:
#   tmux new -s deploy
#   ./02-deploy.sh
#   (If disconnected, reconnect and run: tmux attach -t deploy)
# =============================================================================

set -e

# =============================================================================
# CONFIGURATION
# =============================================================================
PROJECT_ID="vidsynth-demo-proj2025"
REGION="us-central1"
ARTIFACT_REPO="vidsynth-repo"
COMPOSER_ENV="vidsynth-composer"
COMPOSER_IMAGE="composer-2.9.7-airflow-2.9.3"

# Container registry base path
REGISTRY="${REGION}-docker.pkg.dev/${PROJECT_ID}/${ARTIFACT_REPO}"

# Path to services and DAG (relative to this script's location)
PIPELINE_DIR="../VidSynth_Pipeline"
DAG_SOURCE="../VidSynth_Pipeline/airflow/dags/vidsynth_pipeline_dag_DEMO.py"

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================
log() {
    echo ""
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

wait_for_composer() {
    log "Waiting for Composer environment to be ready..."
    while true; do
        STATE=$(gcloud composer environments describe "$COMPOSER_ENV" \
            --location="$REGION" \
            --format="value(state)" 2>/dev/null || echo "CREATING")
        
        if [ "$STATE" = "RUNNING" ]; then
            log "Composer environment is ready!"
            return 0
        elif [ "$STATE" = "ERROR" ]; then
            log "ERROR: Composer environment creation failed"
            exit 1
        else
            echo "  Current state: $STATE (checking again in 60 seconds...)"
            sleep 60
        fi
    done
}

# =============================================================================
# PREREQUISITE CHECKS
# =============================================================================
log "Checking prerequisites..."

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PIPELINE_PATH="$SCRIPT_DIR/$PIPELINE_DIR"
DAG_PATH="$SCRIPT_DIR/$DAG_SOURCE"

if [ ! -d "$PIPELINE_PATH" ]; then
    echo "ERROR: Pipeline directory not found at $PIPELINE_PATH"
    exit 1
fi

if [ ! -f "$DAG_PATH" ]; then
    echo "ERROR: DAG file not found at $DAG_PATH"
    exit 1
fi

# Verify project is set
gcloud config set project "$PROJECT_ID"

log "Prerequisites OK"

# =============================================================================
# STEP 1: START COMPOSER CREATION (ASYNC)
# =============================================================================
log "=========================================="
log "STEP 1: Starting Cloud Composer Creation"
log "=========================================="

if gcloud composer environments describe "$COMPOSER_ENV" --location="$REGION" &> /dev/null; then
    log "Composer environment $COMPOSER_ENV already exists, skipping creation"
    COMPOSER_ALREADY_EXISTS=true
else
    log "Creating Composer environment (async)..."
    log "This will run in background while we deploy Cloud Run services"
    
    gcloud composer environments create "$COMPOSER_ENV" \
        --location="$REGION" \
        --image-version="$COMPOSER_IMAGE" \
        --async
    
    COMPOSER_ALREADY_EXISTS=false
    log "Composer creation initiated"
fi

# =============================================================================
# STEP 2: BUILD AND DEPLOY CLOUD RUN SERVICES
# =============================================================================
log "=========================================="
log "STEP 2: Building and Deploying Cloud Run Services"
log "=========================================="

# Declare associative array to store URLs
declare -A SERVICE_URLS

# -----------------------------------------------------------------------------
# read-service
# -----------------------------------------------------------------------------
log ">>> Building read-service..."
cd "$PIPELINE_PATH/read_service"

gcloud builds submit --tag "${REGISTRY}/read-service"

log ">>> Deploying read-service..."
gcloud run deploy read-service \
    --image "${REGISTRY}/read-service" \
    --region "$REGION" \
    --min-instances 1 \
    --max-instances 3 \
    --memory 512Mi \
    --cpu 1 \
    --allow-unauthenticated

SERVICE_URLS["URL_READ"]=$(gcloud run services describe read-service \
    --region="$REGION" --format="value(status.url)")
log "read-service deployed: ${SERVICE_URLS["URL_READ"]}"

# -----------------------------------------------------------------------------
# preprocess-service
# -----------------------------------------------------------------------------
log ">>> Building preprocess-service..."
cd "$PIPELINE_PATH/preprocess_service"

gcloud builds submit --tag "${REGISTRY}/preprocess-service"

log ">>> Deploying preprocess-service..."
gcloud run deploy preprocess-service \
    --image "${REGISTRY}/preprocess-service:latest" \
    --region "$REGION" \
    --min-instances 1 \
    --max-instances 3 \
    --memory 512Mi \
    --cpu 1 \
    --allow-unauthenticated

SERVICE_URLS["URL_PREPROCESS"]=$(gcloud run services describe preprocess-service \
    --region="$REGION" --format="value(status.url)")
log "preprocess-service deployed: ${SERVICE_URLS["URL_PREPROCESS"]}"

# -----------------------------------------------------------------------------
# validate-service
# -----------------------------------------------------------------------------
log ">>> Building validate-service..."
cd "$PIPELINE_PATH/validate_service"

gcloud builds submit --tag "${REGISTRY}/validate-service"

log ">>> Deploying validate-service..."
gcloud run deploy validate-service \
    --image "${REGISTRY}/validate-service" \
    --region "$REGION" \
    --min-instances 1 \
    --max-instances 3 \
    --memory 512Mi \
    --cpu 1 \
    --allow-unauthenticated

SERVICE_URLS["URL_VALIDATE"]=$(gcloud run services describe validate-service \
    --region="$REGION" --format="value(status.url)")
log "validate-service deployed: ${SERVICE_URLS["URL_VALIDATE"]}"

# -----------------------------------------------------------------------------
# push-service
# -----------------------------------------------------------------------------
log ">>> Building push-service..."
cd "$PIPELINE_PATH/push_service"

gcloud builds submit --tag "${REGISTRY}/push-service"

log ">>> Deploying push-service..."
gcloud run deploy push-service \
    --image "${REGISTRY}/push-service" \
    --region "$REGION" \
    --min-instances 1 \
    --max-instances 3 \
    --memory 512Mi \
    --cpu 1 \
    --allow-unauthenticated

SERVICE_URLS["URL_PUSH"]=$(gcloud run services describe push-service \
    --region="$REGION" --format="value(status.url)")
log "push-service deployed: ${SERVICE_URLS["URL_PUSH"]}"

# =============================================================================
# STEP 3: WAIT FOR COMPOSER TO BE READY
# =============================================================================
log "=========================================="
log "STEP 3: Waiting for Composer Environment"
log "=========================================="

if [ "$COMPOSER_ALREADY_EXISTS" = true ]; then
    log "Composer already existed, checking state..."
fi

wait_for_composer

# =============================================================================
# STEP 4: SET AIRFLOW VARIABLES
# =============================================================================
log "=========================================="
log "STEP 4: Setting Airflow Variables"
log "=========================================="

log "Setting URL_READ..."
gcloud composer environments run "$COMPOSER_ENV" \
    --location="$REGION" \
    variables set -- URL_READ "${SERVICE_URLS["URL_READ"]}/read"

log "Setting URL_PREPROCESS..."
gcloud composer environments run "$COMPOSER_ENV" \
    --location="$REGION" \
    variables set -- URL_PREPROCESS "${SERVICE_URLS["URL_PREPROCESS"]}/preprocess"

log "Setting URL_VALIDATE..."
gcloud composer environments run "$COMPOSER_ENV" \
    --location="$REGION" \
    variables set -- URL_VALIDATE "${SERVICE_URLS["URL_VALIDATE"]}/validate"

log "Setting URL_PUSH..."
gcloud composer environments run "$COMPOSER_ENV" \
    --location="$REGION" \
    variables set -- URL_PUSH "${SERVICE_URLS["URL_PUSH"]}/push"

log "Airflow variables set"

# =============================================================================
# STEP 5: UPLOAD DAG
# =============================================================================
log "=========================================="
log "STEP 5: Uploading DAG"
log "=========================================="

gcloud composer environments storage dags import "$COMPOSER_ENV" \
    --location="$REGION" \
    --source="$DAG_PATH"

log "DAG uploaded"

# =============================================================================
# SUMMARY
# =============================================================================
log "=========================================="
log "DEPLOYMENT COMPLETE"
log "=========================================="

AIRFLOW_URI=$(gcloud composer environments describe "$COMPOSER_ENV" \
    --location="$REGION" \
    --format="value(config.airflowUri)")

echo ""
echo "Cloud Run Services:"
echo "  read-service:       ${SERVICE_URLS["URL_READ"]}"
echo "  preprocess-service: ${SERVICE_URLS["URL_PREPROCESS"]}"
echo "  validate-service:   ${SERVICE_URLS["URL_VALIDATE"]}"
echo "  push-service:       ${SERVICE_URLS["URL_PUSH"]}"
echo ""
echo "Cloud Composer:"
echo "  Environment: $COMPOSER_ENV"
echo "  Airflow UI:  $AIRFLOW_URI"
echo ""
echo "Airflow Variables set:"
echo "  URL_READ, URL_PREPROCESS, URL_VALIDATE, URL_PUSH"
echo ""
echo "NOTE: LLM service not included (handled separately)"
echo ""
echo "To tear down all resources: ./99-teardown.sh"
