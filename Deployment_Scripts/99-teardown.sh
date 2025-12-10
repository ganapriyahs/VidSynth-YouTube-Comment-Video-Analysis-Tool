#!/bin/bash
# =============================================================================
# GCP Project Teardown Script
# Purpose: Clean up all resources created by the bootstrap script
# WARNING: This will DELETE resources. Use with caution.
# =============================================================================

set -e

# =============================================================================
# CONFIGURATION - Must match bootstrap script
# =============================================================================
PROJECT_ID="vidsynth-demo-proj2025"
REGION="us-central1"
ZONE="us-central1-a"
ARTIFACT_REPO="vidsynth-repo"
BUCKET_NAME="vidsynth-demo-model-store"
RESULTS_BUCKET="vidsynth-results"
COMPOSER_ENV="vidsynth-composer"
TGI_SERVICE_NAME="tgi-service"
LLM_SERVICE_NAME="llm-service"
GATEWAY_SERVICE_NAME="gateway-service"
LLM_SETUP_VM="llm-setup-vm"

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# =============================================================================
# CONFIRMATION
# =============================================================================
echo "=========================================="
echo "WARNING: This will delete the following:"
echo "  - Project: $PROJECT_ID"
echo "  - Composer environment: $COMPOSER_ENV"
echo "  - All Cloud Run services"
echo "  - Artifact Registry and images"
echo "  - Storage bucket: $BUCKET_NAME"
echo "=========================================="
echo ""
read -p "Are you sure you want to continue? (type 'yes' to confirm): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "Aborted."
    exit 0
fi

# =============================================================================
# TEARDOWN OPTIONS
# =============================================================================
echo ""
echo "Choose teardown mode:"
echo "  1) Delete entire project (recommended for clean slate)"
echo "  2) Delete resources only, keep project (reuse project ID)"
echo ""
read -p "Enter choice (1 or 2): " MODE

case $MODE in
    1)
        # ---------------------------------------------------------------------
        # Option 1: Delete entire project
        # ---------------------------------------------------------------------
        log "Deleting entire project $PROJECT_ID..."
        gcloud projects delete "$PROJECT_ID" --quiet
        log "Project deleted"
        echo ""
        echo "NOTE: Project ID '$PROJECT_ID' will be unavailable for 30 days."
        echo "      To reuse immediately, choose option 2 next time."
        ;;
    2)
        # ---------------------------------------------------------------------
        # Option 2: Delete resources, keep project
        # ---------------------------------------------------------------------
        log "Setting active project..."
        gcloud config set project "$PROJECT_ID"
        
        # Delete LLM setup VM if still running
        log "Checking for LLM setup VM..."
        if gcloud compute instances describe "$LLM_SETUP_VM" --zone="$ZONE" &> /dev/null; then
            log "  Deleting LLM setup VM..."
            gcloud compute instances delete "$LLM_SETUP_VM" --zone="$ZONE" --quiet
            log "  LLM setup VM deleted"
        else
            log "  LLM setup VM not found, skipping"
        fi
        
        # Delete Composer environment first (most expensive, takes longest)
        log "Checking for Composer environment..."
        if gcloud composer environments describe "$COMPOSER_ENV" --location="$REGION" &> /dev/null; then
            log "  Deleting Composer environment $COMPOSER_ENV (this takes ~10 min)..."
            gcloud composer environments delete "$COMPOSER_ENV" --location="$REGION" --quiet
            log "  Composer environment deleted"
        else
            log "  Composer environment not found, skipping"
        fi
        
        # Delete Cloud Run services (if any)
        log "Checking for Cloud Run services..."
        SERVICES=$(gcloud run services list --region="$REGION" --format="value(name)" 2>/dev/null || true)
        if [ -n "$SERVICES" ]; then
            for svc in $SERVICES; do
                log "  Deleting Cloud Run service: $svc"
                gcloud run services delete "$svc" --region="$REGION" --quiet
            done
        else
            log "  No Cloud Run services found"
        fi
        
        # Delete Artifact Registry images and repo
        log "Deleting Artifact Registry repository..."
        if gcloud artifacts repositories describe "$ARTIFACT_REPO" --location="$REGION" &> /dev/null; then
            # Delete all images first
            gcloud artifacts docker images list "${REGION}-docker.pkg.dev/${PROJECT_ID}/${ARTIFACT_REPO}" \
                --format="value(IMAGE)" 2>/dev/null | while read -r image; do
                log "  Deleting image: $image"
                gcloud artifacts docker images delete "$image" --quiet --delete-tags 2>/dev/null || true
            done
            # Delete repo
            gcloud artifacts repositories delete "$ARTIFACT_REPO" \
                --location="$REGION" --quiet
            log "  Repository deleted"
        else
            log "  Repository not found, skipping"
        fi
        
        # Delete Storage bucket contents and bucket (Model Store)
        log "Deleting model storage bucket..."
        BUCKET_URI="gs://${BUCKET_NAME}"
        if gcloud storage buckets describe "$BUCKET_URI" &> /dev/null; then
            # Delete all objects first
            gcloud storage rm -r "${BUCKET_URI}/**" 2>/dev/null || true
            # Delete bucket
            gcloud storage buckets delete "$BUCKET_URI" --quiet
            log "  Model bucket deleted"
        else
            log "  Model bucket not found, skipping"
        fi
        
        # Delete Storage bucket contents and bucket (Results)
        log "Deleting results storage bucket..."
        RESULTS_BUCKET_URI="gs://${RESULTS_BUCKET}"
        if gcloud storage buckets describe "$RESULTS_BUCKET_URI" &> /dev/null; then
            # Delete all objects first
            gcloud storage rm -r "${RESULTS_BUCKET_URI}/**" 2>/dev/null || true
            # Delete bucket
            gcloud storage buckets delete "$RESULTS_BUCKET_URI" --quiet
            log "  Results bucket deleted"
        else
            log "  Results bucket not found, skipping"
        fi
        
        log "Resources deleted. Project $PROJECT_ID retained."
        echo ""
        echo "You can now re-run 01-bootstrap.sh to recreate resources."
        ;;
    *)
        echo "Invalid choice. Aborted."
        exit 1
        ;;
esac

log "Teardown complete"
