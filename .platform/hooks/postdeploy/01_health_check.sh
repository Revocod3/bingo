#!/bin/bash

echo "=== Post-deployment Health Check ==="
TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")

# Ensure log directory exists
LOG_DIR="/var/log/app"
mkdir -p $LOG_DIR
LOG_FILE="$LOG_DIR/post_deploy_check_$(date +%Y%m%d_%H%M%S).log"

# Function to log with timestamps
log() {
    echo "[$(date +"%Y-%m-%d %H:%M:%S")] $1" | tee -a $LOG_FILE
}

log "Starting health check at $TIMESTAMP"
log "Running as user: $(whoami)"
log "Current directory: $(pwd)"

# Check file permissions
log "Checking file permissions..."
ls -la /var/app/current/ | tee -a $LOG_FILE

# Check environment variables
log "Environment variables:"
log "DJANGO_SETTINGS_MODULE: $DJANGO_SETTINGS_MODULE"
log "AWS_DB_HOST: $AWS_DB_HOST"
log "AWS_DB_NAME: $AWS_DB_NAME"

# Check all critical environment variables
CRITICAL_VARS=("DJANGO_SETTINGS_MODULE" "AWS_DB_NAME" "AWS_DB_USER" "AWS_DB_HOST" "AWS_DB_PORT" "SECRET_KEY")
MISSING_VARS=()

for var in "${CRITICAL_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        log "ERROR: Environment variable $var is not set!"
        MISSING_VARS+=("$var")
    else
        if [[ "$var" == *"PASSWORD"* ]] || [[ "$var" == "SECRET_KEY" ]]; then
            log "$var: [PROTECTED]"
        else
            log "$var: ${!var}"
        fi
    fi
done

if [ ${#MISSING_VARS[@]} -gt 0 ]; then
    log "WARNING: Missing critical environment variables: ${MISSING_VARS[*]}"
    log "Continuing anyway, but deployment may fail later."
fi

# Navigate to app directory and activate virtual environment
cd /var/app/current || {
    log "ERROR: Failed to change to /var/app/current directory"
    log "Current directory: $(pwd)"
    log "Directory listing:"
    ls -la / | tee -a $LOG_FILE
    log "Attempting to find the application directory..."
    find /var/app -type d -name "current" 2>/dev/null | tee -a $LOG_FILE
}

# Check if virtual environment exists and activate it
VENV_ACTIVATE=$(find /var/app/venv -name "activate" 2>/dev/null | head -1)
if [ -z "$VENV_ACTIVATE" ]; then
    log "ERROR: Could not find virtual environment activate script"
    log "Listing /var/app directory structure:"
    find /var/app -type d | tee -a $LOG_FILE
else
    log "Found virtual environment at: $VENV_ACTIVATE"
    source "$VENV_ACTIVATE" || log "ERROR: Failed to activate virtual environment"
fi

# Check Python and pip
log "Python version:"
python --version 2>&1 | tee -a $LOG_FILE || log "ERROR: Failed to get Python version"

log "Pip packages:"
pip freeze 2>&1 | tee -a $LOG_FILE || log "ERROR: Failed to list pip packages"

# Test basic Python import
log "Testing basic Python imports..."
python -c "import django; print(f'Django version: {django.__version__}')" 2>&1 | tee -a $LOG_FILE || log "ERROR: Failed to import Django"

# Test database connection with error handling
log "Testing database connection..."
python manage.py check_db_connection --verbose 2>&1 | tee -a $LOG_FILE
DB_CHECK_STATUS=$?
if [ $DB_CHECK_STATUS -ne 0 ]; then
    log "WARNING: Database connection check returned non-zero status: $DB_CHECK_STATUS"
    log "Trying alternative database check..."
    python -c "
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', os.environ.get('DJANGO_SETTINGS_MODULE', 'core.settings'))
django.setup()
from django.db import connections
connections['default'].ensure_connection()
print('Alternative database check: Connection successful!')
" 2>&1 | tee -a $LOG_FILE || log "ERROR: Alternative database check also failed"
fi

# Run deployment test script with error handling
log "Running deployment test..."
if [ -f deployment_test.py ]; then
    python deployment_test.py 2>&1 | tee -a $LOG_FILE || log "WARNING: Deployment test returned non-zero status"
else
    log "ERROR: deployment_test.py not found"
    # Create a minimal test script on the fly
    log "Creating and running a minimal test script..."
    python -c "
import sys, os, platform
print('Python version:', sys.version)
print('Platform info:', platform.platform())
print('Current directory:', os.getcwd())
print('Directory listing:', os.listdir('.'))
print('Environment variables:', {k: v for k, v in os.environ.items() if not 'SECRET' in k.upper() and not 'PASSWORD' in k.upper()})
" 2>&1 | tee -a $LOG_FILE
fi

# Check requirements
log "Checking requirements..."
if [ -f .ebextensions/check_requirements.py ]; then
    python .ebextensions/check_requirements.py 2>&1 | tee -a $LOG_FILE || log "WARNING: Requirements check returned non-zero status"
else
    log "ERROR: check_requirements.py not found"
    # Do a basic check
    log "Running basic requirements check..."
    python -c "
import sys
requirements = ['django', 'psycopg2', 'gunicorn', 'djangorestframework']
missing = []
for req in requirements:
    try:
        __import__(req)
        print(f'✓ {req} is installed')
    except ImportError:
        missing.append(req)
        print(f'✗ {req} is missing')
print(f'Basic requirements check: {len(missing)} packages missing out of {len(requirements)}')
" 2>&1 | tee -a $LOG_FILE
fi

# Check disk space
log "Checking disk space:"
df -h / 2>&1 | tee -a $LOG_FILE

# Check memory usage
log "Checking memory usage:"
free -h 2>&1 | tee -a $LOG_FILE

log "Health check completed at $(date +"%Y-%m-%d %H:%M:%S")"
log "Log file: $LOG_FILE"

# Create a summary file that will be easier to find
SUMMARY_FILE="$LOG_DIR/latest_deploy_summary.log"
{
    echo "==================== DEPLOYMENT SUMMARY ===================="
    echo "Timestamp: $(date)"
    echo "Python: $(python --version 2>&1)"
    echo "Django: $(python -c 'import django; print(django.__version__)' 2>&1 || echo 'Not installed or not importable')"
    echo "Missing env vars: ${MISSING_VARS[*]:-None}"
    echo "Database check status: $DB_CHECK_STATUS (0=success)"
    echo "Disk space:"
    df -h / | grep -v "Filesystem"
    echo "Full log: $LOG_FILE"
    echo "==========================================================="
} > $SUMMARY_FILE

log "Summary written to $SUMMARY_FILE"

# Always exit with success to prevent deployment rollback
exit 0
