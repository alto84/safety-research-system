#!/bin/bash

###############################################################################
# Safety Research System - Deployment Script
# This script automates the deployment process for the application
###############################################################################

set -e  # Exit on error
set -u  # Exit on undefined variable
set -o pipefail  # Exit on pipe failure

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Configuration
ENVIRONMENT="${1:-staging}"
DEPLOY_TYPE="${2:-rolling}"  # rolling, blue-green, or canary
DRY_RUN="${DRY_RUN:-false}"

# Derived variables
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="${PROJECT_ROOT}/logs/deploy_${ENVIRONMENT}_${TIMESTAMP}.log"

###############################################################################
# Functions
###############################################################################

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $*" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR]${NC} $*" | tee -a "$LOG_FILE"
    exit 1
}

warn() {
    echo -e "${YELLOW}[WARNING]${NC} $*" | tee -a "$LOG_FILE"
}

info() {
    echo -e "${BLUE}[INFO]${NC} $*" | tee -a "$LOG_FILE"
}

check_prerequisites() {
    log "Checking prerequisites..."

    # Check AWS CLI
    if ! command -v aws &> /dev/null; then
        error "AWS CLI not found. Please install it first."
    fi

    # Check Docker
    if ! command -v docker &> /dev/null; then
        error "Docker not found. Please install it first."
    fi

    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        error "AWS credentials not configured or invalid."
    fi

    # Check environment
    if [[ ! "$ENVIRONMENT" =~ ^(dev|staging|production)$ ]]; then
        error "Invalid environment: $ENVIRONMENT. Must be dev, staging, or production."
    fi

    log "Prerequisites check passed ✓"
}

create_backup() {
    log "Creating backup before deployment..."

    if [[ "$DRY_RUN" == "true" ]]; then
        info "DRY RUN: Would create backup"
        return
    fi

    # Run backup script
    bash "${SCRIPT_DIR}/backup.sh" "$ENVIRONMENT"

    log "Backup created ✓"
}

build_and_push_image() {
    log "Building and pushing Docker image..."

    local IMAGE_TAG="$ENVIRONMENT-$(git rev-parse --short HEAD)"
    local REGISTRY="ghcr.io/your-org/safety-research-system"
    local FULL_IMAGE="$REGISTRY:$IMAGE_TAG"

    if [[ "$DRY_RUN" == "true" ]]; then
        info "DRY RUN: Would build and push $FULL_IMAGE"
        return
    fi

    # Build image
    cd "$PROJECT_ROOT"
    docker build -t "$FULL_IMAGE" .

    # Tag as latest for this environment
    docker tag "$FULL_IMAGE" "$REGISTRY:$ENVIRONMENT-latest"

    # Push images
    docker push "$FULL_IMAGE"
    docker push "$REGISTRY:$ENVIRONMENT-latest"

    # Export for use in deployment
    export DEPLOY_IMAGE="$FULL_IMAGE"

    log "Image built and pushed: $FULL_IMAGE ✓"
}

run_pre_deployment_tests() {
    log "Running pre-deployment tests..."

    if [[ "$DRY_RUN" == "true" ]]; then
        info "DRY RUN: Would run tests"
        return
    fi

    # Run smoke tests
    cd "$PROJECT_ROOT"
    python -m pytest tests/ -v -k "smoke" || error "Pre-deployment tests failed"

    log "Pre-deployment tests passed ✓"
}

update_ecs_service() {
    log "Updating ECS service..."

    local CLUSTER_NAME="safety-research-${ENVIRONMENT}"
    local SERVICE_NAME="safety-research-api"

    if [[ "$DRY_RUN" == "true" ]]; then
        info "DRY RUN: Would update ECS service $CLUSTER_NAME/$SERVICE_NAME"
        return
    fi

    # Update service with new image
    aws ecs update-service \
        --cluster "$CLUSTER_NAME" \
        --service "$SERVICE_NAME" \
        --force-new-deployment \
        --region us-east-1

    log "ECS service update initiated ✓"
}

wait_for_deployment() {
    log "Waiting for deployment to complete..."

    local CLUSTER_NAME="safety-research-${ENVIRONMENT}"
    local SERVICE_NAME="safety-research-api"
    local MAX_WAIT=600  # 10 minutes
    local WAIT_INTERVAL=10
    local ELAPSED=0

    if [[ "$DRY_RUN" == "true" ]]; then
        info "DRY RUN: Would wait for deployment"
        return
    fi

    while [ $ELAPSED -lt $MAX_WAIT ]; do
        # Get service status
        local RUNNING_COUNT=$(aws ecs describe-services \
            --cluster "$CLUSTER_NAME" \
            --services "$SERVICE_NAME" \
            --region us-east-1 \
            --query 'services[0].runningCount' \
            --output text)

        local DESIRED_COUNT=$(aws ecs describe-services \
            --cluster "$CLUSTER_NAME" \
            --services "$SERVICE_NAME" \
            --region us-east-1 \
            --query 'services[0].desiredCount' \
            --output text)

        if [ "$RUNNING_COUNT" -eq "$DESIRED_COUNT" ]; then
            log "Deployment completed successfully ✓"
            return 0
        fi

        info "Waiting for deployment... ($RUNNING_COUNT/$DESIRED_COUNT running)"
        sleep $WAIT_INTERVAL
        ELAPSED=$((ELAPSED + WAIT_INTERVAL))
    done

    error "Deployment timed out after ${MAX_WAIT}s"
}

run_smoke_tests() {
    log "Running smoke tests..."

    if [[ "$DRY_RUN" == "true" ]]; then
        info "DRY RUN: Would run smoke tests"
        return
    fi

    # Get ALB DNS name
    local ALB_DNS=$(aws elbv2 describe-load-balancers \
        --names "safety-research-${ENVIRONMENT}-alb" \
        --region us-east-1 \
        --query 'LoadBalancers[0].DNSName' \
        --output text)

    # Test health endpoint
    local HEALTH_URL="http://${ALB_DNS}/health"
    local RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "$HEALTH_URL")

    if [ "$RESPONSE" -ne 200 ]; then
        error "Health check failed. HTTP status: $RESPONSE"
    fi

    log "Smoke tests passed ✓"
}

rollback_on_failure() {
    warn "Deployment failed. Rolling back..."

    if [[ "$DRY_RUN" == "true" ]]; then
        info "DRY RUN: Would rollback"
        return
    fi

    bash "${SCRIPT_DIR}/rollback.sh" "$ENVIRONMENT"
}

send_notification() {
    local STATUS="$1"
    local MESSAGE="$2"

    log "Sending notification: $STATUS - $MESSAGE"

    # Send Slack notification (if configured)
    if [ -n "${SLACK_WEBHOOK:-}" ]; then
        curl -X POST "$SLACK_WEBHOOK" \
            -H 'Content-Type: application/json' \
            -d "{\"text\":\"Deployment $STATUS: $MESSAGE\"}"
    fi

    # Send email notification (if configured)
    if [ -n "${NOTIFICATION_EMAIL:-}" ]; then
        echo "$MESSAGE" | mail -s "Deployment $STATUS - $ENVIRONMENT" "$NOTIFICATION_EMAIL"
    fi
}

###############################################################################
# Main Deployment Flow
###############################################################################

main() {
    log "=========================================="
    log "Starting deployment to $ENVIRONMENT"
    log "Deploy type: $DEPLOY_TYPE"
    log "Dry run: $DRY_RUN"
    log "=========================================="

    # Create logs directory
    mkdir -p "${PROJECT_ROOT}/logs"

    # Trap errors and rollback
    trap 'rollback_on_failure' ERR

    # Deployment steps
    check_prerequisites
    create_backup
    build_and_push_image
    run_pre_deployment_tests
    update_ecs_service
    wait_for_deployment
    run_smoke_tests

    log "=========================================="
    log "Deployment completed successfully! ✓"
    log "=========================================="

    # Send success notification
    send_notification "SUCCESS" "Deployment to $ENVIRONMENT completed successfully"

    # Print deployment summary
    cat << EOF

Deployment Summary:
-------------------
Environment: $ENVIRONMENT
Deploy Type: $DEPLOY_TYPE
Image: ${DEPLOY_IMAGE:-N/A}
Timestamp: $TIMESTAMP
Log File: $LOG_FILE

Next Steps:
1. Monitor CloudWatch dashboards
2. Check application logs
3. Verify key user journeys
4. Watch for any alerts

EOF
}

# Run main function
main "$@"
