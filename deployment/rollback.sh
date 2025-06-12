#!/bin/bash

# Rollback Script for Telegram Bot
# Provides quick rollback capabilities for failed deployments

set -euo pipefail

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="${SCRIPT_DIR}/config/deploy.conf"
BACKUP_DIR="${SCRIPT_DIR}/backups"
LOG_FILE="${SCRIPT_DIR}/logs/rollback_$(date +%Y%m%d_%H%M%S).log"

# Default values
BACKUP_FILE=""
GIT_COMMIT=""
RESTORE_DATABASE=true
RESTORE_CODE=true
RESTART_SERVICE=true
DRY_RUN=false
FORCE=false
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
    else
        error_exit "Configuration file not found: $CONFIG_FILE"
    fi
}

# Show usage
usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Rollback Script for Telegram Bot

OPTIONS:
    --backup-file FILE      Database backup file to restore
    --git-commit COMMIT     Git commit hash to rollback to
    --no-database           Skip database restoration
    --no-code               Skip code rollback
    --no-service            Skip service restart
    --dry-run               Simulate rollback without changes
    --force                 Force rollback without confirmations
    --verbose               Enable verbose output
    --list-backups          List available backup files
    --list-commits          List recent Git commits
    --help                  Show this help message

EXAMPLES:
    $0 --backup-file "backup_20240108_010000.sql.gz"
    $0 --git-commit "abc123def456"
    $0 --no-database --git-commit "HEAD~1"
    $0 --list-backups

EOF
}

# Parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --backup-file)
                BACKUP_FILE="$2"
                shift 2
                ;;
            --git-commit)
                GIT_COMMIT="$2"
                shift 2
                ;;
            --no-database)
                RESTORE_DATABASE=false
                shift
                ;;
            --no-code)
                RESTORE_CODE=false
                shift
                ;;
            --no-service)
                RESTART_SERVICE=false
                shift
                ;;
            --dry-run)
                DRY_RUN=true
                shift
                ;;
            --force)
                FORCE=true
                shift
                ;;
            --verbose)
                VERBOSE=true
                shift
                ;;
            --list-backups)
                list_backups
                exit 0
                ;;
            --list-commits)
                list_commits
                exit 0
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

# List available backups
list_backups() {
    log "INFO" "Available backup files:"
    
    if [[ -d "$BACKUP_DIR" ]]; then
        find "$BACKUP_DIR" -name "backup_*.sql*" -type f | sort -r | while read -r backup; do
            local size=$(du -h "$backup" | cut -f1)
            local date=$(basename "$backup" | sed 's/backup_\([0-9]\{8\}_[0-9]\{6\}\).*/\1/' | sed 's/_/ /')
            echo "  📁 $(basename "$backup") (${size}, ${date})"
        done
    else
        log "WARNING" "Backup directory not found: $BACKUP_DIR"
    fi
    
    # List S3 backups if configured
    if [[ -n "${S3_BUCKET:-}" ]] && command -v aws &> /dev/null; then
        log "INFO" "Available S3 backups:"
        aws s3 ls "s3://${S3_BUCKET}/backups/" --recursive | grep "backup_" | sort -r | head -10 | while read -r line; do
            local file=$(echo "$line" | awk '{print $4}')
            local size=$(echo "$line" | awk '{print $3}')
            echo "  ☁️  $(basename "$file") (${size})"
        done
    fi
}

# List recent commits
list_commits() {
    local repo_dir="${DEPLOY_PATH}/${REPO_NAME}"
    
    if [[ ! -d "$repo_dir" ]]; then
        error_exit "Repository directory not found: $repo_dir"
    fi
    
    log "INFO" "Recent Git commits:"
    cd "$repo_dir"
    git log --oneline -10 | while read -r line; do
        echo "  🔗 $line"
    done
}

# Confirm rollback
confirm_rollback() {
    if [[ "$FORCE" == "true" ]] || [[ "$DRY_RUN" == "true" ]]; then
        return 0
    fi
    
    log "WARNING" "This will rollback the current deployment!"
    
    if [[ "$RESTORE_DATABASE" == "true" ]] && [[ -n "$BACKUP_FILE" ]]; then
        log "WARNING" "Database will be restored from: $BACKUP_FILE"
    fi
    
    if [[ "$RESTORE_CODE" == "true" ]] && [[ -n "$GIT_COMMIT" ]]; then
        log "WARNING" "Code will be rolled back to: $GIT_COMMIT"
    fi
    
    echo -n "Are you sure you want to continue? (yes/no): "
    read -r response
    
    if [[ "$response" != "yes" ]]; then
        log "INFO" "Rollback cancelled by user"
        exit 0
    fi
}

# Stop service
stop_service() {
    local service_name="${REPO_NAME}.service"
    
    log "INFO" "Stopping service: $service_name"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log "INFO" "[DRY RUN] Would stop service: $service_name"
        return 0
    fi
    
    if systemctl is-active --quiet "$service_name"; then
        sudo systemctl stop "$service_name"
        log "SUCCESS" "Service stopped"
    else
        log "INFO" "Service was not running"
    fi
}

# Restore database
restore_database() {
    if [[ "$RESTORE_DATABASE" != "true" ]]; then
        log "INFO" "Skipping database restoration"
        return 0
    fi
    
    if [[ -z "$BACKUP_FILE" ]]; then
        log "WARNING" "No backup file specified, skipping database restoration"
        return 0
    fi
    
    log "INFO" "Restoring database from backup..."
    
    # Find backup file
    local backup_path=""
    if [[ -f "$BACKUP_FILE" ]]; then
        backup_path="$BACKUP_FILE"
    elif [[ -f "$BACKUP_DIR/$BACKUP_FILE" ]]; then
        backup_path="$BACKUP_DIR/$BACKUP_FILE"
    else
        # Try to download from S3
        if [[ -n "${S3_BUCKET:-}" ]] && command -v aws &> /dev/null; then
            log "INFO" "Downloading backup from S3..."
            backup_path="/tmp/$(basename "$BACKUP_FILE")"
            if aws s3 cp "s3://${S3_BUCKET}/backups/$(basename "$BACKUP_FILE")" "$backup_path"; then
                log "SUCCESS" "Backup downloaded from S3"
            else
                error_exit "Failed to download backup from S3"
            fi
        else
            error_exit "Backup file not found: $BACKUP_FILE"
        fi
    fi
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log "INFO" "[DRY RUN] Would restore database from: $backup_path"
        return 0
    fi
    
    # Prepare backup file for restoration
    local restore_file="$backup_path"
    
    # Decompress if needed
    if [[ "$backup_path" == *.gz ]]; then
        log "INFO" "Decompressing backup file..."
        restore_file="/tmp/restore_$(date +%s).sql"
        gunzip -c "$backup_path" > "$restore_file"
    fi
    
    # Decrypt if needed
    if [[ "$backup_path" == *.gpg ]]; then
        log "INFO" "Decrypting backup file..."
        local decrypted_file="/tmp/restore_$(date +%s).sql"
        gpg --decrypt "$restore_file" > "$decrypted_file"
        restore_file="$decrypted_file"
    fi
    
    # Create a backup of current database before restoration
    log "INFO" "Creating safety backup of current database..."
    local safety_backup="${BACKUP_DIR}/safety_backup_$(date +%Y%m%d_%H%M%S).sql"
    mkdir -p "$BACKUP_DIR"
    pg_dump "$DATABASE_URL" > "$safety_backup"
    log "SUCCESS" "Safety backup created: $safety_backup"
    
    # Restore database
    log "INFO" "Restoring database..."
    if psql "$DATABASE_URL" < "$restore_file"; then
        log "SUCCESS" "Database restored successfully"
    else
        error_exit "Database restoration failed"
    fi
    
    # Cleanup temporary files
    if [[ "$restore_file" != "$backup_path" ]]; then
        rm -f "$restore_file"
    fi
    
    if [[ "$backup_path" == "/tmp/"* ]]; then
        rm -f "$backup_path"
    fi
}

# Rollback code
rollback_code() {
    if [[ "$RESTORE_CODE" != "true" ]]; then
        log "INFO" "Skipping code rollback"
        return 0
    fi
    
    local repo_dir="${DEPLOY_PATH}/${REPO_NAME}"
    
    if [[ ! -d "$repo_dir" ]]; then
        error_exit "Repository directory not found: $repo_dir"
    fi
    
    log "INFO" "Rolling back code..."
    
    cd "$repo_dir"
    
    # Determine target commit
    local target_commit="$GIT_COMMIT"
    if [[ -z "$target_commit" ]]; then
        # Default to previous commit
        target_commit="HEAD~1"
        log "INFO" "No commit specified, using previous commit: $target_commit"
    fi
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log "INFO" "[DRY RUN] Would rollback code to: $target_commit"
        return 0
    fi
    
    # Stash any local changes
    if ! git diff --quiet; then
        log "INFO" "Stashing local changes..."
        git stash push -m "Rollback stash $(date)"
    fi
    
    # Checkout target commit
    log "INFO" "Checking out commit: $target_commit"
    if git checkout "$target_commit"; then
        log "SUCCESS" "Code rolled back to: $target_commit"
    else
        error_exit "Failed to checkout commit: $target_commit"
    fi
    
    # Update dependencies
    log "INFO" "Updating dependencies..."
    if [[ -d ".venv" ]]; then
        source .venv/bin/activate
        uv sync
        log "SUCCESS" "Dependencies updated"
    else
        log "WARNING" "Virtual environment not found, skipping dependency update"
    fi
}

# Start service
start_service() {
    if [[ "$RESTART_SERVICE" != "true" ]]; then
        log "INFO" "Skipping service restart"
        return 0
    fi
    
    local service_name="${REPO_NAME}.service"
    
    log "INFO" "Starting service: $service_name"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log "INFO" "[DRY RUN] Would start service: $service_name"
        return 0
    fi
    
    # Reload systemd configuration
    sudo systemctl daemon-reload
    
    # Start service
    sudo systemctl start "$service_name"
    
    # Wait and check status
    sleep 5
    if systemctl is-active --quiet "$service_name"; then
        log "SUCCESS" "Service started successfully"
    else
        error_exit "Service failed to start"
    fi
}

# Verify rollback
verify_rollback() {
    log "INFO" "Verifying rollback..."
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log "INFO" "[DRY RUN] Would verify rollback"
        return 0
    fi
    
    # Run health check if available
    if [[ -f "${SCRIPT_DIR}/health-check.sh" ]]; then
        if "${SCRIPT_DIR}/health-check.sh" --post-deployment; then
            log "SUCCESS" "Rollback verification passed"
        else
            log "ERROR" "Rollback verification failed"
            return 1
        fi
    else
        log "WARNING" "Health check script not found, skipping verification"
    fi
}

# Main rollback function
main() {
    # Create logs directory
    mkdir -p "${SCRIPT_DIR}/logs"
    
    log "INFO" "Starting rollback process..."
    log "INFO" "Rollback script: $0"
    log "INFO" "Arguments: $*"
    
    # Load configuration and parse arguments
    load_config
    parse_args "$@"
    
    # Validate inputs
    if [[ "$RESTORE_DATABASE" == "true" ]] && [[ -z "$BACKUP_FILE" ]]; then
        error_exit "Database restoration requested but no backup file specified"
    fi
    
    if [[ "$RESTORE_CODE" == "true" ]] && [[ -z "$GIT_COMMIT" ]]; then
        log "WARNING" "No Git commit specified, will use HEAD~1"
    fi
    
    # Confirm rollback
    confirm_rollback
    
    # Main rollback process
    stop_service
    restore_database
    rollback_code
    start_service
    verify_rollback
    
    log "SUCCESS" "Rollback completed successfully!"
    
    # Show current status
    local service_name="${REPO_NAME}.service"
    log "INFO" "Service status: $(systemctl is-active "$service_name")"
    
    if [[ "$RESTORE_CODE" == "true" ]]; then
        local repo_dir="${DEPLOY_PATH}/${REPO_NAME}"
        cd "$repo_dir"
        local current_commit=$(git rev-parse --short HEAD)
        log "INFO" "Current commit: $current_commit"
    fi
}

# Run main function with all arguments
main "$@"