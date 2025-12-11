#!/bin/bash
# =============================================================================
# GCP Project Bootstrap Script
# Purpose: Initialize a fresh GCP project with all required services for vidsynth
# Prerequisites: gcloud CLI installed and authenticated (gcloud auth login)
# =============================================================================

set -e  # Exit on any error

# =============================================================================
# CONFIGURATION - Modify these variables
# =============================================================================
BILLING_ACCOUNT="${BILLING_ACCOUNT:?Error: BILLING_ACCOUNT environment variable must be set}"
PROJECT_ID="vidsynth-demo-proj2025"
REGION="us-central1"
ARTIFACT_REPO="vidsynth-repo"
BUCKET_NAME="vidsynth-demo-model-store"
RESULTS_BUCKET="vidsynth-results"

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

check_prerequisites() {
    log "Checking prerequisites..."
    
    if ! command -v gcloud &> /dev/null; then
        echo "ERROR: gcloud CLI not installed. Install from https://cloud.google.com/sdk/docs/install"
        exit 1
    fi
    
    # Check if authenticated
    if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | head -1 | grep -q "@"; then
        echo "ERROR: Not authenticated. Run 'gcloud auth login' first."
        exit 1
    fi
    
    log "Prerequisites OK"
}

# =============================================================================
# MAIN SETUP
# =============================================================================

check_prerequisites

log "=========================================="
log "Starting GCP Bootstrap"
log "Project ID: $PROJECT_ID"
log "Region: $REGION"
log "Billing Account: $BILLING_ACCOUNT"
log "=========================================="

# -----------------------------------------------------------------------------
# Step 1: Create Project
# -----------------------------------------------------------------------------
log "Step 1: Creating project..."
if gcloud projects describe "$PROJECT_ID" &> /dev/null; then
    log "Project $PROJECT_ID already exists, skipping creation"
else
    gcloud projects create "$PROJECT_ID" --name="VidSynth Demo Project"
    log "Project created"
fi

# -----------------------------------------------------------------------------
# Step 2: Link Billing Account
# -----------------------------------------------------------------------------
log "Step 2: Linking billing account..."
gcloud billing projects link "$PROJECT_ID" --billing-account="$BILLING_ACCOUNT"
log "Billing linked"

# -----------------------------------------------------------------------------
# Step 3: Set Active Project
# -----------------------------------------------------------------------------
log "Step 3: Setting active project..."
gcloud config set project "$PROJECT_ID"
log "Active project set to $PROJECT_ID"

# -----------------------------------------------------------------------------
# Step 4: Enable APIs
# -----------------------------------------------------------------------------
log "Step 4: Enabling APIs (this may take a few minutes)..."

APIS=(
    "artifactregistry.googleapis.com"
    "run.googleapis.com"
    "composer.googleapis.com"
    "cloudbuild.googleapis.com"
    "storage.googleapis.com"
    "compute.googleapis.com"
)

for api in "${APIS[@]}"; do
    log "  Enabling $api..."
    gcloud services enable "$api" --project="$PROJECT_ID"
done
log "All APIs enabled"

# -----------------------------------------------------------------------------
# Step 5: Grant Composer Service Agent Required Role
# -----------------------------------------------------------------------------
log "Step 5: Granting Composer Service Agent permissions..."

# Get project number
PROJECT_NUMBER=$(gcloud projects describe "$PROJECT_ID" --format="value(projectNumber)")
COMPOSER_SA="service-${PROJECT_NUMBER}@cloudcomposer-accounts.iam.gserviceaccount.com"

# Grant the ServiceAgentV2Ext role (required for Composer 2)
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:${COMPOSER_SA}" \
    --role="roles/composer.ServiceAgentV2Ext" \
    --condition=None \
    --quiet

log "Composer service agent permissions granted"

# -----------------------------------------------------------------------------
# Step 6: Create Artifact Registry Repository
# -----------------------------------------------------------------------------
log "Step 6: Creating Artifact Registry repository..."
if gcloud artifacts repositories describe "$ARTIFACT_REPO" --location="$REGION" &> /dev/null; then
    log "Repository $ARTIFACT_REPO already exists, skipping"
else
    gcloud artifacts repositories create "$ARTIFACT_REPO" \
        --repository-format=docker \
        --location="$REGION" \
        --description="VidSynth container images"
    log "Artifact Registry repository created"
fi

# -----------------------------------------------------------------------------
# Step 7: Create Storage Bucket (Model Store)
# -----------------------------------------------------------------------------
log "Step 7: Creating model storage bucket..."
BUCKET_URI="gs://${BUCKET_NAME}"
if gcloud storage buckets describe "$BUCKET_URI" &> /dev/null; then
    log "Bucket $BUCKET_NAME already exists, skipping"
else
    gcloud storage buckets create "$BUCKET_URI" \
        --location="$REGION" \
        --uniform-bucket-level-access
    log "Model storage bucket created"
fi

# -----------------------------------------------------------------------------
# Step 8: Create Storage Bucket (Results)
# -----------------------------------------------------------------------------
log "Step 8: Creating results storage bucket..."
RESULTS_BUCKET_URI="gs://${RESULTS_BUCKET}"
if gcloud storage buckets describe "$RESULTS_BUCKET_URI" &> /dev/null; then
    log "Bucket $RESULTS_BUCKET already exists, skipping"
else
    gcloud storage buckets create "$RESULTS_BUCKET_URI" \
        --location="$REGION" \
        --uniform-bucket-level-access
    log "Results storage bucket created"
fi

# -----------------------------------------------------------------------------
# Step 9: Configure Docker Authentication
# -----------------------------------------------------------------------------
log "Step 9: Configuring Docker authentication for Artifact Registry..."
gcloud auth configure-docker "${REGION}-docker.pkg.dev" --quiet
log "Docker authentication configured"

# =============================================================================
# SUMMARY
# =============================================================================
log "=========================================="
log "Bootstrap Complete!"
log "=========================================="
echo ""
echo "Project ID:        $PROJECT_ID"
echo "Region:            $REGION"
echo "Artifact Registry: ${REGION}-docker.pkg.dev/${PROJECT_ID}/${ARTIFACT_REPO}"
echo "Model Bucket:      gs://${BUCKET_NAME}"
echo "Results Bucket:    gs://${RESULTS_BUCKET}"
echo ""
echo "Next steps:"
echo "  1. Run 02-setup-llm.sh to deploy the TGI service"
echo "  2. Run 03-deploy.sh to deploy other services and Composer"
echo ""
echo "To tear down this project, run: ./99-teardown.sh"