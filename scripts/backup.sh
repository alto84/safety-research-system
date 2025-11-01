#!/bin/bash

###############################################################################
# Safety Research System - Database Backup Script
# Creates backups of PostgreSQL database and uploads to S3
###############################################################################

set -e
set -u
set -o pipefail

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Configuration
ENVIRONMENT="${1:-production}"
BACKUP_TYPE="${2:-manual}"  # manual or automated
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/tmp/backups"
BACKUP_FILENAME="safety_research_${ENVIRONMENT}_${TIMESTAMP}.sql.gz"
S3_BUCKET="safety-research-backups"
S3_PREFIX="${ENVIRONMENT}/database"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-90}"

# RDS Configuration
RDS_INSTANCE="safety-research-${ENVIRONMENT}-db"
DB_NAME="safety_research"

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $*"
}

error() {
    echo -e "${RED}[ERROR]${NC} $*"
    exit 1
}

info() {
    echo -e "${YELLOW}[INFO]${NC} $*"
}

# Create backup directory
mkdir -p "$BACKUP_DIR"

log "Starting backup process for $ENVIRONMENT environment..."

# Option 1: Use RDS automated snapshots (recommended)
create_rds_snapshot() {
    log "Creating RDS snapshot..."

    local SNAPSHOT_ID="safety-research-${ENVIRONMENT}-manual-${TIMESTAMP}"

    aws rds create-db-snapshot \
        --db-instance-identifier "$RDS_INSTANCE" \
        --db-snapshot-identifier "$SNAPSHOT_ID" \
        --tags "Key=Environment,Value=${ENVIRONMENT}" "Key=Type,Value=${BACKUP_TYPE}" \
        --region us-east-1

    log "RDS snapshot created: $SNAPSHOT_ID"

    # Wait for snapshot to complete
    log "Waiting for snapshot to complete..."
    aws rds wait db-snapshot-completed \
        --db-snapshot-identifier "$SNAPSHOT_ID" \
        --region us-east-1

    log "Snapshot completed ✓"
}

# Option 2: Logical backup with pg_dump
create_logical_backup() {
    log "Creating logical backup with pg_dump..."

    # Get database credentials from Secrets Manager
    local SECRET_ARN="arn:aws:secretsmanager:us-east-1:123456789012:secret:${ENVIRONMENT}/database/credentials"
    local CREDS=$(aws secretsmanager get-secret-value --secret-id "$SECRET_ARN" --query SecretString --output text)

    local DB_HOST=$(echo "$CREDS" | jq -r '.host')
    local DB_USER=$(echo "$CREDS" | jq -r '.username')
    local DB_PASS=$(echo "$CREDS" | jq -r '.password')

    # Set password in environment
    export PGPASSWORD="$DB_PASS"

    # Create backup
    log "Dumping database..."
    pg_dump -h "$DB_HOST" \
            -U "$DB_USER" \
            -d "$DB_NAME" \
            -F c \
            -b \
            -v \
            -f "${BACKUP_DIR}/${BACKUP_FILENAME%.gz}"

    # Compress backup
    log "Compressing backup..."
    gzip "${BACKUP_DIR}/${BACKUP_FILENAME%.gz}"

    # Clear password from environment
    unset PGPASSWORD

    log "Backup created: ${BACKUP_DIR}/${BACKUP_FILENAME}"
}

# Upload to S3
upload_to_s3() {
    log "Uploading backup to S3..."

    local S3_PATH="s3://${S3_BUCKET}/${S3_PREFIX}/${BACKUP_FILENAME}"

    aws s3 cp "${BACKUP_DIR}/${BACKUP_FILENAME}" "$S3_PATH" \
        --storage-class STANDARD_IA \
        --server-side-encryption AES256 \
        --metadata "environment=${ENVIRONMENT},type=${BACKUP_TYPE},timestamp=${TIMESTAMP}"

    log "Backup uploaded to: $S3_PATH"
}

# Verify backup
verify_backup() {
    log "Verifying backup..."

    local S3_PATH="s3://${S3_BUCKET}/${S3_PREFIX}/${BACKUP_FILENAME}"

    # Check if file exists in S3
    if aws s3 ls "$S3_PATH" > /dev/null 2>&1; then
        local SIZE=$(aws s3 ls "$S3_PATH" | awk '{print $3}')
        log "Backup verified. Size: ${SIZE} bytes ✓"
    else
        error "Backup verification failed. File not found in S3."
    fi
}

# Clean up old backups
cleanup_old_backups() {
    log "Cleaning up old backups (retention: ${RETENTION_DAYS} days)..."

    local CUTOFF_DATE=$(date -d "${RETENTION_DAYS} days ago" +%s)

    aws s3api list-objects-v2 \
        --bucket "$S3_BUCKET" \
        --prefix "$S3_PREFIX/" \
        --query "Contents[?LastModified<='$(date -d @${CUTOFF_DATE} --iso-8601=seconds)'].Key" \
        --output text | \
    while read -r key; do
        if [ -n "$key" ]; then
            log "Deleting old backup: $key"
            aws s3 rm "s3://${S3_BUCKET}/${key}"
        fi
    done

    log "Cleanup completed ✓"
}

# Clean up local files
cleanup_local() {
    log "Cleaning up local backup files..."
    rm -f "${BACKUP_DIR}/${BACKUP_FILENAME}"
    log "Local cleanup completed ✓"
}

# Main backup process
main() {
    log "=========================================="
    log "Database Backup - $ENVIRONMENT"
    log "Type: $BACKUP_TYPE"
    log "=========================================="

    # Create RDS snapshot (recommended for production)
    create_rds_snapshot

    # Optionally create logical backup for point-in-time restore
    # create_logical_backup
    # upload_to_s3
    # verify_backup

    # Cleanup
    cleanup_old_backups
    # cleanup_local

    log "=========================================="
    log "Backup completed successfully! ✓"
    log "=========================================="

    # Send notification
    if [ -n "${SLACK_WEBHOOK:-}" ]; then
        curl -X POST "$SLACK_WEBHOOK" \
            -H 'Content-Type: application/json' \
            -d "{\"text\":\"Database backup completed for $ENVIRONMENT\"}"
    fi
}

main "$@"
