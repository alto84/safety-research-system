#!/bin/bash

###############################################################################
# Safety Research System - Rollback Script
# Rolls back to the previous stable deployment
###############################################################################

set -e
set -u
set -o pipefail

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
ENVIRONMENT="${1:-production}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="/tmp/rollback_${ENVIRONMENT}_${TIMESTAMP}.log"

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

confirm_rollback() {
    warn "=========================================="
    warn "WARNING: You are about to rollback $ENVIRONMENT"
    warn "=========================================="

    if [[ "$ENVIRONMENT" == "production" ]]; then
        read -p "Type 'ROLLBACK PRODUCTION' to confirm: " confirmation
        if [[ "$confirmation" != "ROLLBACK PRODUCTION" ]]; then
            error "Rollback cancelled"
        fi
    else
        read -p "Confirm rollback to $ENVIRONMENT? (yes/no): " confirmation
        if [[ "$confirmation" != "yes" ]]; then
            error "Rollback cancelled"
        fi
    fi

    log "Rollback confirmed"
}

get_previous_task_definition() {
    log "Getting previous task definition..."

    local CLUSTER_NAME="safety-research-${ENVIRONMENT}"
    local SERVICE_NAME="safety-research-api"

    # Get service details
    local SERVICE_JSON=$(aws ecs describe-services \
        --cluster "$CLUSTER_NAME" \
        --services "$SERVICE_NAME" \
        --region us-east-1)

    # Get current task definition
    local CURRENT_TASK_DEF=$(echo "$SERVICE_JSON" | jq -r '.services[0].taskDefinition')

    log "Current task definition: $CURRENT_TASK_DEF"

    # Get task definition family
    local TASK_FAMILY=$(echo "$CURRENT_TASK_DEF" | cut -d'/' -f2 | cut -d':' -f1)

    # List task definitions and get previous version
    local PREVIOUS_TASK_DEF=$(aws ecs list-task-definitions \
        --family-prefix "$TASK_FAMILY" \
        --sort DESC \
        --max-items 2 \
        --region us-east-1 \
        | jq -r '.taskDefinitionArns[1]')

    if [ -z "$PREVIOUS_TASK_DEF" ] || [ "$PREVIOUS_TASK_DEF" == "null" ]; then
        error "Could not find previous task definition"
    fi

    log "Previous task definition: $PREVIOUS_TASK_DEF"

    echo "$PREVIOUS_TASK_DEF"
}

perform_rollback() {
    log "Performing rollback..."

    local CLUSTER_NAME="safety-research-${ENVIRONMENT}"
    local SERVICE_NAME="safety-research-api"
    local PREVIOUS_TASK_DEF=$(get_previous_task_definition)

    # Update service with previous task definition
    aws ecs update-service \
        --cluster "$CLUSTER_NAME" \
        --service "$SERVICE_NAME" \
        --task-definition "$PREVIOUS_TASK_DEF" \
        --region us-east-1

    log "Rollback initiated ✓"
}

wait_for_rollback() {
    log "Waiting for rollback to complete..."

    local CLUSTER_NAME="safety-research-${ENVIRONMENT}"
    local SERVICE_NAME="safety-research-api"
    local MAX_WAIT=600
    local WAIT_INTERVAL=10
    local ELAPSED=0

    while [ $ELAPSED -lt $MAX_WAIT ]; do
        local STATUS=$(aws ecs describe-services \
            --cluster "$CLUSTER_NAME" \
            --services "$SERVICE_NAME" \
            --region us-east-1 \
            --query 'services[0].deployments[0].rolloutState' \
            --output text)

        if [ "$STATUS" == "COMPLETED" ]; then
            log "Rollback completed successfully ✓"
            return 0
        fi

        info "Waiting for rollback... Status: $STATUS"
        sleep $WAIT_INTERVAL
        ELAPSED=$((ELAPSED + WAIT_INTERVAL))
    done

    error "Rollback timed out after ${MAX_WAIT}s"
}

verify_rollback() {
    log "Verifying rollback..."

    local CLUSTER_NAME="safety-research-${ENVIRONMENT}"
    local ALB_DNS=$(aws elbv2 describe-load-balancers \
        --names "safety-research-${ENVIRONMENT}-alb" \
        --region us-east-1 \
        --query 'LoadBalancers[0].DNSName' \
        --output text)

    # Test health endpoint
    local HEALTH_URL="http://${ALB_DNS}/health"
    local RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "$HEALTH_URL")

    if [ "$RESPONSE" -ne 200 ]; then
        error "Health check failed after rollback. HTTP status: $RESPONSE"
    fi

    log "Health check passed ✓"
}

send_notification() {
    log "Sending rollback notification..."

    local MESSAGE="Rollback completed for $ENVIRONMENT environment"

    # Send Slack notification
    if [ -n "${SLACK_WEBHOOK:-}" ]; then
        curl -X POST "$SLACK_WEBHOOK" \
            -H 'Content-Type: application/json' \
            -d "{\"text\":\"⚠️ ROLLBACK: $MESSAGE\",\"username\":\"Deployment Bot\"}"
    fi

    # Send email notification
    if [ -n "${NOTIFICATION_EMAIL:-}" ]; then
        echo "$MESSAGE" | mail -s "ROLLBACK - $ENVIRONMENT" "$NOTIFICATION_EMAIL"
    fi
}

main() {
    log "=========================================="
    log "Starting rollback for $ENVIRONMENT"
    log "=========================================="

    confirm_rollback
    perform_rollback
    wait_for_rollback
    verify_rollback
    send_notification

    log "=========================================="
    log "Rollback completed successfully! ✓"
    log "=========================================="

    cat << EOF

Rollback Summary:
-----------------
Environment: $ENVIRONMENT
Timestamp: $TIMESTAMP
Log File: $LOG_FILE

Next Steps:
1. Monitor application metrics
2. Review logs for any issues
3. Investigate root cause of failure
4. Plan fix and redeployment

EOF
}

main "$@"
