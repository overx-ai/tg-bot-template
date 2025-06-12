#!/bin/bash

# Database Backup Script for Telegram Bot
# Creates PostgreSQL dumps with S3 upload and rotation

set -euo pipefail

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="${SCRIPT_DIR}/config/deploy.conf"
BACKUP_DIR="${SCRIPT_DIR}/backups"
LOG_FILE="${SCRIPT_DIR}/logs/backup_$(date +%Y%m%d_%H%M%S).log"

# Default values
DB_URL=""
S3_BUCKET=""
S3_REGION="us-east-1"
BACKUP_RETENTION=3
DRY_RUN=false
COMPRESS=true
ENCRYPT=false
VERBOSE=false

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    local level=$1
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    echo -e "${timestamp} [${level}] ${message}" | tee -a "${LOG_FILE}"
    
    case $level in
        "ERROR") echo -e "${RED}❌ ${message}${NC}" ;;
        "SUCCESS") echo -e "${GREEN}✅ ${message}${NC}" ;;
        "WARNING") echo -e "${YELLOW}⚠️  ${message}${NC}" ;;
        "INFO") echo -e "${BLUE}ℹ️  ${message}${NC}" ;;
    esac
}

# Error handler
error_exit() {
    log "ERROR" "$1"
    exit 1
}

# Load configuration
load_config() {
    if [[ -f "$CONFIG_FILE" ]]; then
        log "INFO" "Loading configuration from $CONFIG_FILE"
        source "$CONFIG_FILE"
    fi
}

# Show usage
usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Database Backup Script for Telegram Bot

OPTIONS:
    --db-url URL            Database connection URL
    --s3-bucket BUCKET      S3 bucket for backup storage
    --s3-region REGION      S3 region (default: us-east-1)
    --retention COUNT       Number of backups to keep (default: 3)
    --compress              Enable compression (default: true)
    --no-compress           Disable compression
    --encrypt               Enable encryption
    --dry-run               Simulate backup without creating files
    --verbose               Enable verbose output
    --help                  Show this help message

EXAMPLES:
    $0 --db-url "postgresql://user:pass@host:5432/db"
    $0 --s3-bucket "my-backups" --retention 5
    $0 --dry-run --verbose

EOF
}

# Parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --db-url)
                DB_URL="$2"
                shift 2
                ;;
            --s3-bucket)
                S3_BUCKET="$2"
                shift 2
                ;;
            --s3-region)
                S3_REGION="$2"
                shift 2
                ;;
            --retention)
                BACKUP_RETENTION="$2"
                shift 2
                ;;
            --compress)
                COMPRESS=true
                shift
                ;;
            --no-compress)
                COMPRESS=false
                shift
                ;;
            --encrypt)
                ENCRYPT=true
                shift
                ;;
            --dry-run)
                DRY_RUN=true
                shift
                ;;
            --verbose)
                VERBOSE=true
                shift
                ;;
            --help)
                usage
                exit 0
                ;;
            *)
                error_exit "Unknown option: $1"
                ;;
        esac
    done
}

# Check prerequisites
check_prerequisites() {
    log "INFO" "Checking prerequisites..."
    
    # Check required commands
    local required_commands=("pg_dump" "psql")
    for cmd in "${required_commands[@]}"; do
        if ! command -v "$cmd" &> /dev/null; then
            error_exit "Required command not found: $cmd"
        fi
    done
    
    # Check compression tools
    if [[ "$COMPRESS" == "true" ]] && ! command -v "gzip" &> /dev/null; then
        error_exit "gzip not found but compression is enabled"
    fi
    
    # Check encryption tools
    if [[ "$ENCRYPT" == "true" ]] && ! command -v "gpg" &> /dev/null; then
        error_exit "gpg not found but encryption is enabled"
    fi
    
    # Check AWS CLI if S3 is enabled
    if [[ -n "$S3_BUCKET" ]] && ! command -v "aws" &> /dev/null; then
        error_exit "AWS CLI not found but S3 upload is enabled"
    fi
    
    # Check database URL
    if [[ -z "$DB_URL" ]]; then
        # Try to get from environment or config
        if [[ -n "${DATABASE_URL:-}" ]]; then
            DB_URL="$DATABASE_URL"
        else
            error_exit "Database URL not specified"
        fi
    fi
    
    log "SUCCESS" "Prerequisites check passed"
}

# Test database connection
test_connection() {
    log "INFO" "Testing database connection..."
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log "INFO" "[DRY RUN] Would test connection to: ${DB_URL%%@*}@***"
        return 0
    fi
    
    # Test connection with a simple query
    if psql "$DB_URL" -c "SELECT 1;" &> /dev/null; then
        log "SUCCESS" "Database connection successful"
    else
        error_exit "Database connection failed"
    fi
}

# Create database backup
create_backup() {
    log "INFO" "Creating database backup..."
    
    # Create backup directory
    mkdir -p "$BACKUP_DIR"
    
    # Generate backup filename
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_file="${BACKUP_DIR}/backup_${timestamp}.sql"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log "INFO" "[DRY RUN] Would create backup: $backup_file"
        return 0
    fi
    
    # Create the backup
    log "INFO" "Dumping database to: $backup_file"
    if pg_dump "$DB_URL" > "$backup_file"; then
        log "SUCCESS" "Database dump created: $backup_file"
    else
        error_exit "Database dump failed"
    fi
    
    # Get backup size
    local backup_size=$(du -h "$backup_file" | cut -f1)
    log "INFO" "Backup size: $backup_size"
    
    # Compress if enabled
    if [[ "$COMPRESS" == "true" ]]; then
        log "INFO" "Compressing backup..."
        gzip "$backup_file"
        backup_file="${backup_file}.gz"
        local compressed_size=$(du -h "$backup_file" | cut -f1)
        log "SUCCESS" "Backup compressed: $compressed_size"
    fi
    
    # Encrypt if enabled
    if [[ "$ENCRYPT" == "true" ]]; then
        log "INFO" "Encrypting backup..."
        if [[ -n "${GPG_RECIPIENT:-}" ]]; then
            gpg --trust-model always --encrypt -r "$GPG_RECIPIENT" "$backup_file"
            rm "$backup_file"
            backup_file="${backup_file}.gpg"
            log "SUCCESS" "Backup encrypted"
        else
            log "WARNING" "GPG_RECIPIENT not set, skipping encryption"
        fi
    fi
    
    # Store backup filename for other functions
    LATEST_BACKUP="$backup_file"
}

# Upload to S3
upload_to_s3() {
    if [[ -z "$S3_BUCKET" ]]; then
        log "INFO" "S3 upload disabled"
        return 0
    fi
    
    log "INFO" "Uploading backup to S3..."
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log "INFO" "[DRY RUN] Would upload to: s3://${S3_BUCKET}/$(basename "$LATEST_BACKUP")"
        return 0
    fi
    
    # Upload to S3
    local s3_key="backups/$(basename "$LATEST_BACKUP")"
    if aws s3 cp "$LATEST_BACKUP" "s3://${S3_BUCKET}/${s3_key}" --region "$S3_REGION"; then
        log "SUCCESS" "Backup uploaded to S3: s3://${S3_BUCKET}/${s3_key}"
    else
        error_exit "S3 upload failed"
    fi
    
    # Set lifecycle policy if not exists
    set_s3_lifecycle
}

# Set S3 lifecycle policy
set_s3_lifecycle() {
    log "INFO" "Checking S3 lifecycle policy..."
    
    # Check if lifecycle policy exists
    if aws s3api get-bucket-lifecycle-configuration --bucket "$S3_BUCKET" --region "$S3_REGION" &> /dev/null; then
        log "INFO" "S3 lifecycle policy already exists"
        return 0
    fi
    
    # Create lifecycle policy
    local lifecycle_policy=$(cat << EOF
{
    "Rules": [
        {
            "ID": "backup-retention",
            "Status": "Enabled",
            "Filter": {
                "Prefix": "backups/"
            },
            "Expiration": {
                "Days": 30
            }
        }
    ]
}
EOF
)
    
    echo "$lifecycle_policy" > "/tmp/lifecycle.json"
    
    if aws s3api put-bucket-lifecycle-configuration \
        --bucket "$S3_BUCKET" \
        --region "$S3_REGION" \
        --lifecycle-configuration file:///tmp/lifecycle.json; then
        log "SUCCESS" "S3 lifecycle policy created"
    else
        log "WARNING" "Failed to create S3 lifecycle policy"
    fi
    
    rm -f "/tmp/lifecycle.json"
}

# Cleanup old backups
cleanup_old_backups() {
    log "INFO" "Cleaning up old backups..."
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log "INFO" "[DRY RUN] Would keep $BACKUP_RETENTION latest backups"
        return 0
    fi
    
    # Local cleanup
    local backup_count=$(find "$BACKUP_DIR" -name "backup_*.sql*" -type f | wc -l)
    if [[ $backup_count -gt $BACKUP_RETENTION ]]; then
        log "INFO" "Removing old local backups (keeping $BACKUP_RETENTION)"
        find "$BACKUP_DIR" -name "backup_*.sql*" -type f | sort | head -n -$BACKUP_RETENTION | xargs rm -f
        log "SUCCESS" "Old local backups removed"
    fi
    
    # S3 cleanup
    if [[ -n "$S3_BUCKET" ]]; then
        log "INFO" "Cleaning up old S3 backups..."
        
        # List S3 objects and remove old ones
        local s3_objects=$(aws s3api list-objects-v2 \
            --bucket "$S3_BUCKET" \
            --prefix "backups/backup_" \
            --query "Contents[?Size > \`0\`].[Key,LastModified]" \
            --output text | sort -k2 | head -n -$BACKUP_RETENTION | cut -f1)
        
        if [[ -n "$s3_objects" ]]; then
            echo "$s3_objects" | while read -r key; do
                if [[ -n "$key" ]]; then
                    aws s3 rm "s3://${S3_BUCKET}/${key}" --region "$S3_REGION"
                    log "INFO" "Removed old S3 backup: $key"
                fi
            done
            log "SUCCESS" "Old S3 backups removed"
        fi
    fi
}

# Verify backup integrity
verify_backup() {
    if [[ "$DRY_RUN" == "true" ]]; then
        log "INFO" "[DRY RUN] Would verify backup integrity"
        return 0
    fi
    
    log "INFO" "Verifying backup integrity..."
    
    local test_file="$LATEST_BACKUP"
    
    # Decompress if needed for verification
    if [[ "$test_file" == *.gz ]]; then
        local temp_file="/tmp/backup_verify.sql"
        gunzip -c "$test_file" > "$temp_file"
        test_file="$temp_file"
    fi
    
    # Check if file contains SQL content
    if grep -q "PostgreSQL database dump" "$test_file" 2>/dev/null; then
        log "SUCCESS" "Backup integrity verified"
    else
        error_exit "Backup integrity check failed"
    fi
    
    # Cleanup temp file
    if [[ "$test_file" == "/tmp/backup_verify.sql" ]]; then
        rm -f "$test_file"
    fi
}

# Main backup function
main() {
    # Create directories
    mkdir -p "${SCRIPT_DIR}/logs"
    mkdir -p "$BACKUP_DIR"
    
    log "INFO" "Starting database backup process..."
    log "INFO" "Backup script: $0"
    log "INFO" "Arguments: $*"
    
    # Load configuration and parse arguments
    load_config
    parse_args "$@"
    
    # Main backup process
    check_prerequisites
    test_connection
    create_backup
    verify_backup
    upload_to_s3
    cleanup_old_backups
    
    log "SUCCESS" "Database backup completed successfully!"
    if [[ -n "${LATEST_BACKUP:-}" ]]; then
        log "INFO" "Backup file: $LATEST_BACKUP"
    fi
}

# Run main function with all arguments
main "$@"