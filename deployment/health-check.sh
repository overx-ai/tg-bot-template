#!/bin/bash

# Health Check Script for Telegram Bot
# Performs comprehensive health checks for bot and database

set -euo pipefail

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="${SCRIPT_DIR}/config/deploy.conf"
LOG_FILE="${SCRIPT_DIR}/logs/health_$(date +%Y%m%d_%H%M%S).log"

# Default values
BOT_TOKEN=""
DB_URL=""
SERVICE_NAME=""
TIMEOUT=30
PRE_DEPLOYMENT=false
POST_DEPLOYMENT=false
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
        
        # Set defaults from config
        SERVICE_NAME="${REPO_NAME:-telegram-bot}"
        BOT_TOKEN="${TELEGRAM_BOT_TOKEN:-}"
        DB_URL="${DATABASE_URL:-}"
    fi
}

# Show usage
usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Health Check Script for Telegram Bot

OPTIONS:
    --bot-token TOKEN       Telegram bot token
    --db-url URL           Database connection URL
    --service-name NAME    Systemd service name
    --timeout SECONDS      Timeout for checks (default: 30)
    --pre-deployment       Run pre-deployment checks
    --post-deployment      Run post-deployment checks
    --verbose              Enable verbose output
    --help                 Show this help message

EXAMPLES:
    $0 --pre-deployment
    $0 --post-deployment
    $0 --bot-token "123:ABC" --db-url "postgresql://..."

EOF
}

# Parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --bot-token)
                BOT_TOKEN="$2"
                shift 2
                ;;
            --db-url)
                DB_URL="$2"
                shift 2
                ;;
            --service-name)
                SERVICE_NAME="$2"
                shift 2
                ;;
            --timeout)
                TIMEOUT="$2"
                shift 2
                ;;
            --pre-deployment)
                PRE_DEPLOYMENT=true
                shift
                ;;
            --post-deployment)
                POST_DEPLOYMENT=true
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

# Check system resources
check_system_resources() {
    log "INFO" "Checking system resources..."
    
    # Check disk space
    local disk_usage=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
    if [[ $disk_usage -gt 90 ]]; then
        log "ERROR" "Disk usage is ${disk_usage}% (critical)"
        return 1
    elif [[ $disk_usage -gt 80 ]]; then
        log "WARNING" "Disk usage is ${disk_usage}% (high)"
    else
        log "SUCCESS" "Disk usage is ${disk_usage}% (normal)"
    fi
    
    # Check memory usage
    local mem_usage=$(free | awk 'NR==2{printf "%.0f", $3*100/$2}')
    if [[ $mem_usage -gt 90 ]]; then
        log "ERROR" "Memory usage is ${mem_usage}% (critical)"
        return 1
    elif [[ $mem_usage -gt 80 ]]; then
        log "WARNING" "Memory usage is ${mem_usage}% (high)"
    else
        log "SUCCESS" "Memory usage is ${mem_usage}% (normal)"
    fi
    
    # Check load average
    local load_avg=$(uptime | awk -F'load average:' '{print $2}' | awk '{print $1}' | sed 's/,//')
    local cpu_cores=$(nproc)
    local load_threshold=$(echo "$cpu_cores * 2" | bc -l)
    
    if (( $(echo "$load_avg > $load_threshold" | bc -l) )); then
        log "WARNING" "Load average is ${load_avg} (high for ${cpu_cores} cores)"
    else
        log "SUCCESS" "Load average is ${load_avg} (normal for ${cpu_cores} cores)"
    fi
    
    return 0
}

# Check database connectivity
check_database() {
    log "INFO" "Checking database connectivity..."
    
    if [[ -z "$DB_URL" ]]; then
        log "WARNING" "Database URL not provided, skipping database check"
        return 0
    fi
    
    # Test basic connection
    if timeout "$TIMEOUT" psql "$DB_URL" -c "SELECT 1;" &> /dev/null; then
        log "SUCCESS" "Database connection successful"
    else
        log "ERROR" "Database connection failed"
        return 1
    fi
    
    # Check database size
    local db_size=$(psql "$DB_URL" -t -c "SELECT pg_size_pretty(pg_database_size(current_database()));" 2>/dev/null | xargs)
    if [[ -n "$db_size" ]]; then
        log "INFO" "Database size: $db_size"
    fi
    
    # Check active connections
    local active_connections=$(psql "$DB_URL" -t -c "SELECT count(*) FROM pg_stat_activity WHERE state = 'active';" 2>/dev/null | xargs)
    if [[ -n "$active_connections" ]]; then
        log "INFO" "Active database connections: $active_connections"
    fi
    
    return 0
}

# Check Telegram bot API
check_bot_api() {
    log "INFO" "Checking Telegram bot API..."
    
    if [[ -z "$BOT_TOKEN" ]]; then
        log "WARNING" "Bot token not provided, skipping bot API check"
        return 0
    fi
    
    # Test bot API with getMe
    local api_url="https://api.telegram.org/bot${BOT_TOKEN}/getMe"
    local response=$(timeout "$TIMEOUT" curl -s "$api_url" 2>/dev/null || echo "")
    
    if [[ -n "$response" ]] && echo "$response" | jq -e '.ok == true' &> /dev/null; then
        local bot_username=$(echo "$response" | jq -r '.result.username')
        log "SUCCESS" "Bot API accessible (username: @${bot_username})"
    else
        log "ERROR" "Bot API check failed"
        return 1
    fi
    
    return 0
}

# Check systemd service
check_service() {
    log "INFO" "Checking systemd service..."
    
    if [[ -z "$SERVICE_NAME" ]]; then
        log "WARNING" "Service name not provided, skipping service check"
        return 0
    fi
    
    # Check if service exists
    if ! systemctl list-unit-files | grep -q "${SERVICE_NAME}.service"; then
        log "WARNING" "Service ${SERVICE_NAME}.service not found"
        return 0
    fi
    
    # Check service status
    if systemctl is-active --quiet "${SERVICE_NAME}.service"; then
        log "SUCCESS" "Service ${SERVICE_NAME}.service is active"
        
        # Get service uptime
        local uptime=$(systemctl show "${SERVICE_NAME}.service" --property=ActiveEnterTimestamp --value)
        if [[ -n "$uptime" ]]; then
            log "INFO" "Service started: $uptime"
        fi
        
        # Check for recent errors in logs
        local error_count=$(journalctl -u "${SERVICE_NAME}.service" --since "1 hour ago" --grep "ERROR" --no-pager -q | wc -l)
        if [[ $error_count -gt 0 ]]; then
            log "WARNING" "Found $error_count errors in service logs (last hour)"
        fi
        
    else
        local service_status=$(systemctl is-active "${SERVICE_NAME}.service")
        log "ERROR" "Service ${SERVICE_NAME}.service is $service_status"
        return 1
    fi
    
    return 0
}

# Check network connectivity
check_network() {
    log "INFO" "Checking network connectivity..."
    
    # Check internet connectivity
    if timeout 10 ping -c 1 8.8.8.8 &> /dev/null; then
        log "SUCCESS" "Internet connectivity available"
    else
        log "ERROR" "No internet connectivity"
        return 1
    fi
    
    # Check Telegram API reachability
    if timeout 10 curl -s https://api.telegram.org &> /dev/null; then
        log "SUCCESS" "Telegram API reachable"
    else
        log "ERROR" "Telegram API unreachable"
        return 1
    fi
    
    return 0
}

# Check file permissions
check_permissions() {
    log "INFO" "Checking file permissions..."
    
    local repo_dir="${DEPLOY_PATH}/${REPO_NAME}"
    
    if [[ ! -d "$repo_dir" ]]; then
        log "WARNING" "Repository directory not found: $repo_dir"
        return 0
    fi
    
    # Check if .env file exists and is readable
    if [[ -f "$repo_dir/.env" ]]; then
        if [[ -r "$repo_dir/.env" ]]; then
            log "SUCCESS" "Environment file is readable"
        else
            log "ERROR" "Environment file is not readable"
            return 1
        fi
    else
        log "WARNING" "Environment file not found"
    fi
    
    # Check Python virtual environment
    if [[ -d "$repo_dir/.venv" ]]; then
        if [[ -x "$repo_dir/.venv/bin/python" ]]; then
            log "SUCCESS" "Python virtual environment is accessible"
        else
            log "ERROR" "Python virtual environment is not executable"
            return 1
        fi
    else
        log "WARNING" "Python virtual environment not found"
    fi
    
    return 0
}

# Check dependencies
check_dependencies() {
    log "INFO" "Checking dependencies..."
    
    local repo_dir="${DEPLOY_PATH}/${REPO_NAME}"
    
    if [[ ! -d "$repo_dir" ]]; then
        log "WARNING" "Repository directory not found, skipping dependency check"
        return 0
    fi
    
    cd "$repo_dir"
    
    # Check if virtual environment exists
    if [[ ! -d ".venv" ]]; then
        log "WARNING" "Virtual environment not found"
        return 0
    fi
    
    source .venv/bin/activate
    
    # Check critical dependencies
    local critical_deps=("python-telegram-bot" "sqlalchemy" "alembic" "asyncpg")
    for dep in "${critical_deps[@]}"; do
        if python -c "import $dep" 2>/dev/null; then
            log "SUCCESS" "Dependency $dep is available"
        else
            log "ERROR" "Critical dependency $dep is missing"
            return 1
        fi
    done
    
    return 0
}

# Run pre-deployment checks
run_pre_deployment_checks() {
    log "INFO" "Running pre-deployment health checks..."
    
    local failed_checks=0
    
    check_system_resources || ((failed_checks++))
    check_network || ((failed_checks++))
    check_database || ((failed_checks++))
    
    if [[ $failed_checks -eq 0 ]]; then
        log "SUCCESS" "All pre-deployment checks passed"
        return 0
    else
        log "ERROR" "$failed_checks pre-deployment check(s) failed"
        return 1
    fi
}

# Run post-deployment checks
run_post_deployment_checks() {
    log "INFO" "Running post-deployment health checks..."
    
    local failed_checks=0
    
    check_system_resources || ((failed_checks++))
    check_network || ((failed_checks++))
    check_database || ((failed_checks++))
    check_bot_api || ((failed_checks++))
    check_service || ((failed_checks++))
    check_permissions || ((failed_checks++))
    check_dependencies || ((failed_checks++))
    
    if [[ $failed_checks -eq 0 ]]; then
        log "SUCCESS" "All post-deployment checks passed"
        return 0
    else
        log "ERROR" "$failed_checks post-deployment check(s) failed"
        return 1
    fi
}

# Main health check function
main() {
    # Create logs directory
    mkdir -p "${SCRIPT_DIR}/logs"
    
    log "INFO" "Starting health check process..."
    log "INFO" "Health check script: $0"
    log "INFO" "Arguments: $*"
    
    # Load configuration and parse arguments
    load_config
    parse_args "$@"
    
    # Check prerequisites
    local required_commands=("curl" "jq" "systemctl" "psql")
    for cmd in "${required_commands[@]}"; do
        if ! command -v "$cmd" &> /dev/null; then
            log "WARNING" "Command not found: $cmd (some checks may be skipped)"
        fi
    done
    
    # Run appropriate checks
    if [[ "$PRE_DEPLOYMENT" == "true" ]]; then
        run_pre_deployment_checks
    elif [[ "$POST_DEPLOYMENT" == "true" ]]; then
        run_post_deployment_checks
    else
        # Run all checks by default
        run_post_deployment_checks
    fi
}

# Run main function with all arguments
main "$@"