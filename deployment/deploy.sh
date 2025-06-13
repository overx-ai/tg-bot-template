#!/bin/bash

# Telegram Bot Deployment Script
# Simple, effective deployment with health checks

set -euo pipefail

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="${SCRIPT_DIR}/config/deploy.conf"
LOG_FILE="${SCRIPT_DIR}/logs/deploy_$(date +%Y%m%d_%H%M%S).log"

# Default values
REPO_URL=""
BRANCH="main"
ENV_FILE=""
DRY_RUN=false
FORCE=false
ROLLBACK=false
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
        log "WARNING" "Configuration file not found: $CONFIG_FILE"
        log "INFO" "Using default values and command line arguments"
    fi
}

# Show usage
usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Telegram Bot Deployment Script

OPTIONS:
    --repo-url URL          Git repository URL
    --branch BRANCH         Branch to deploy (default: main)
    --env-file FILE         Path to environment file
    --dry-run               Simulate deployment without changes
    --force                 Skip health checks and force deployment
    --rollback FILE         Rollback using specified backup file
    --verbose               Enable verbose output
    --help                  Show this help message

EXAMPLES:
    $0 --repo-url "git@github.com:user/repo.git"
    $0 --dry-run
    $0 --rollback "backup_20240108_010000.sql"

EOF
}

# Parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --repo-url)
                REPO_URL="$2"
                shift 2
                ;;
            --branch)
                BRANCH="$2"
                shift 2
                ;;
            --env-file)
                ENV_FILE="$2"
                shift 2
                ;;
            --dry-run)
                DRY_RUN=true
                shift
                ;;
            --force)
                FORCE=true
                shift
                ;;
            --rollback)
                ROLLBACK=true
                ROLLBACK_FILE="$2"
                shift 2
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
    local required_commands=("git" "uv" "python3" "systemctl" "pg_dump" "psql")
    for cmd in "${required_commands[@]}"; do
        if ! command -v "$cmd" &> /dev/null; then
            error_exit "Required command not found: $cmd"
        fi
    done
    
    # Check configuration variables
    if [[ -z "$REPO_URL" ]]; then
        error_exit "Repository URL not specified"
    fi
    
    if [[ -z "$DEPLOY_PATH" ]]; then
        error_exit "DEPLOY_PATH not configured"
    fi
    
    log "SUCCESS" "Prerequisites check passed"
}

# Pre-deployment health check
health_check() {
    if [[ "$FORCE" == "true" ]]; then
        log "WARNING" "Skipping health check (--force enabled)"
        return 0
    fi
    
    log "INFO" "Running pre-deployment health check..."
    
    if [[ -f "${SCRIPT_DIR}/health-check.sh" ]]; then
        if "${SCRIPT_DIR}/health-check.sh" --pre-deployment; then
            log "SUCCESS" "Health check passed"
        else
            error_exit "Health check failed. Use --force to override"
        fi
    else
        log "WARNING" "Health check script not found, skipping"
    fi
}

# Deploy code
deploy_code() {
    log "INFO" "Deploying code..."
    
    local repo_dir="${DEPLOY_PATH}/${REPO_NAME}"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log "INFO" "[DRY RUN] Would deploy to: $repo_dir"
        return 0
    fi
    
    # Create deploy directory if it doesn't exist
    if [[ ! -d "$DEPLOY_PATH" ]]; then
        log "INFO" "Creating deploy directory: $DEPLOY_PATH"
        mkdir -p "$DEPLOY_PATH"
    fi
    
    # Clone or update repository
    if [[ -d "$repo_dir" ]]; then
        log "INFO" "Updating existing repository..."
        cd "$repo_dir"
        git fetch origin
        git checkout "$BRANCH"
        git pull origin "$BRANCH"
    else
        log "INFO" "Cloning repository..."
        cd "$DEPLOY_PATH"
        git clone "$REPO_URL" "$REPO_NAME"
        cd "$repo_dir"
        git checkout "$BRANCH"
    fi
    
    # Setup Python environment
    log "INFO" "Setting up Python environment..."
    if [[ ! -d ".venv" ]]; then
        uv venv
    fi
    
    source .venv/bin/activate
    uv sync
    
    log "SUCCESS" "Code deployment completed"
}

# Setup environment
setup_environment() {
    log "INFO" "Setting up environment..."
    
    local repo_dir="${DEPLOY_PATH}/${REPO_NAME}"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log "INFO" "[DRY RUN] Would setup environment in: $repo_dir"
        return 0
    fi
    
    # Copy environment file
    if [[ -n "$ENV_FILE" ]] && [[ -f "$ENV_FILE" ]]; then
        log "INFO" "Copying environment file..."
        cp "$ENV_FILE" "$repo_dir/.env"
    elif [[ -f "${ENV_FILE_PATH}" ]]; then
        log "INFO" "Copying environment file from configured path..."
        cp "${ENV_FILE_PATH}" "$repo_dir/.env"
    else
        log "WARNING" "No environment file specified or found"
    fi
    
    # Generate systemd service file
    generate_service_file
    
    log "SUCCESS" "Environment setup completed"
}

# Generate systemd service file
generate_service_file() {
    log "INFO" "Generating systemd service file..."
    
    local service_name="${REPO_NAME}.service"
    local service_file="/etc/systemd/system/${service_name}"
    local template_file="${SCRIPT_DIR}/templates/bot.service.template"
    
    if [[ ! -f "$template_file" ]]; then
        error_exit "Service template not found: $template_file"
    fi
    
    # Replace template variables
    local working_dir="${DEPLOY_PATH}/${REPO_NAME}"
    local python_path="${working_dir}/.venv/bin/python"
    local main_script="${working_dir}/telegram_bot_template/main.py"
    
    sed -e "s|\${BOT_NAME}|${REPO_NAME}|g" \
        -e "s|\${BOT_DESCRIPTION}|${BOT_DESCRIPTION:-Telegram Bot}|g" \
        -e "s|\${WORKING_DIR}|${working_dir}|g" \
        -e "s|\${PYTHON_PATH}|${python_path}|g" \
        -e "s|\${MAIN_SCRIPT}|${main_script}|g" \
        -e "s|\${USER}|${SERVICE_USER}|g" \
        "$template_file" > "/tmp/${service_name}"
    
    # Install service file
    sudo mv "/tmp/${service_name}" "$service_file"
    sudo chown root:root "$service_file"
    sudo chmod 644 "$service_file"
    
    log "SUCCESS" "Service file generated: $service_file"
}

# Run database migrations
run_migrations() {
    log "INFO" "Running database migrations..."
    
    local repo_dir="${DEPLOY_PATH}/${REPO_NAME}"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log "INFO" "[DRY RUN] Would run migrations in: $repo_dir"
        return 0
    fi
    
    cd "$repo_dir"
    source .venv/bin/activate
    
    # Run Alembic migrations
    if [[ -f "alembic.ini" ]]; then
        log "INFO" "Running Alembic migrations..."
        alembic upgrade head
        log "SUCCESS" "Database migrations completed"
    else
        log "WARNING" "No alembic.ini found, skipping migrations"
    fi
}

# Manage systemd service
manage_service() {
    log "INFO" "Managing systemd service..."
    
    local service_name="${REPO_NAME}.service"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log "INFO" "[DRY RUN] Would manage service: $service_name"
        return 0
    fi
    
    # Reload systemd
    sudo systemctl daemon-reload
    
    # Enable service
    sudo systemctl enable "$service_name"
    
    # Restart service
    if systemctl is-active --quiet "$service_name"; then
        log "INFO" "Restarting service..."
        sudo systemctl restart "$service_name"
    else
        log "INFO" "Starting service..."
        sudo systemctl start "$service_name"
    fi
    
    # Check service status
    sleep 5
    if systemctl is-active --quiet "$service_name"; then
        log "SUCCESS" "Service is running"
    else
        error_exit "Service failed to start"
    fi
}

# Post-deployment health check
post_deployment_check() {
    log "INFO" "Running post-deployment health check..."
    
    if [[ -f "${SCRIPT_DIR}/health-check.sh" ]]; then
        if "${SCRIPT_DIR}/health-check.sh" --post-deployment; then
            log "SUCCESS" "Post-deployment health check passed"
        else
            error_exit "Post-deployment health check failed"
        fi
    else
        log "WARNING" "Health check script not found, skipping"
    fi
}

# Cleanup
cleanup() {
    log "INFO" "Cleaning up..."
    
    # Remove old log files (keep last 10)
    find "${SCRIPT_DIR}/logs" -name "deploy_*.log" -type f | sort -r | tail -n +11 | xargs rm -f 2>/dev/null || true
    
    log "SUCCESS" "Cleanup completed"
}

# Rollback function
rollback() {
    if [[ "$ROLLBACK" != "true" ]]; then
        return 0
    fi
    
    log "INFO" "Starting rollback process..."
    
    if [[ -f "${SCRIPT_DIR}/rollback.sh" ]]; then
        if "${SCRIPT_DIR}/rollback.sh" --backup-file "$ROLLBACK_FILE"; then
            log "SUCCESS" "Rollback completed"
        else
            error_exit "Rollback failed"
        fi
    else
        error_exit "Rollback script not found: ${SCRIPT_DIR}/rollback.sh"
    fi
}

# Main deployment function
main() {
    # Create logs directory
    mkdir -p "${SCRIPT_DIR}/logs"
    
    log "INFO" "Starting deployment process..."
    log "INFO" "Deployment script: $0"
    log "INFO" "Arguments: $*"
    
    # Load configuration and parse arguments
    load_config
    parse_args "$@"
    
    # Handle rollback
    if [[ "$ROLLBACK" == "true" ]]; then
        rollback
        exit 0
    fi
    
    # Main deployment process
    check_prerequisites
    health_check
    deploy_code
    setup_environment
    run_migrations
    manage_service
    post_deployment_check
    cleanup
    
    log "SUCCESS" "Deployment completed successfully!"
    log "INFO" "Service status: $(systemctl is-active ${REPO_NAME}.service)"
    log "INFO" "Logs: journalctl -u ${REPO_NAME}.service -f"
}

# Run main function with all arguments
main "$@"