#!/bin/bash

echo "=== Pre-deployment Check ==="
LOG_DIR="/var/log/app"
mkdir -p $LOG_DIR
LOG_FILE="$LOG_DIR/pre_deploy_check_$(date +%Y%m%d_%H%M%S).log"

# Function to log with timestamps
log() {
    echo "[$(date +"%Y-%m-%d %H:%M:%S")] $1" | tee -a $LOG_FILE
}

log "Starting pre-deployment checks"
log "Checking Python version compatibility..."

# Check Python version compatibility
python3 --version 2>&1 | tee -a $LOG_FILE || {
    log "ERROR: Python3 not found or not executable"
    log "This might cause deployment issues"
}

# Check disk space before deployment
log "Checking available disk space..."
df -h / | tee -a $LOG_FILE

# Check memory availability
log "Checking memory resources..."
free -h | tee -a $LOG_FILE

# Check networking to database (if already configured)
if [ -n "$AWS_DB_HOST" ] && [ -n "$AWS_DB_PORT" ]; then
    log "Testing database host connectivity..."
    timeout 5 bash -c "</dev/tcp/$AWS_DB_HOST/$AWS_DB_PORT" 2>/dev/null
    if [ $? -eq 0 ]; then
        log "Network connection to database ($AWS_DB_HOST:$AWS_DB_PORT) successful"
    else
        log "WARNING: Cannot establish TCP connection to $AWS_DB_HOST:$AWS_DB_PORT"
        log "This might cause deployment database connectivity issues"
    fi
fi

# Check directory permissions
log "Checking directory permissions..."
ls -la /var/app/ 2>/dev/null | tee -a $LOG_FILE || log "Cannot access /var/app/ yet"

log "Pre-deployment checks completed"

# Always exit with success to allow deployment to proceed
exit 0
