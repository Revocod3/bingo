#!/bin/bash

echo "=== Elastic Beanstalk Environment Diagnostic Tool ==="
echo "Running diagnostics at $(date)"

# Create log file
LOG_FILE="/tmp/eb_diagnosis_$(date +%Y%m%d_%H%M%S).log"
echo "Logging details to $LOG_FILE"

# Function to log both to console and file
log() {
    echo "$@" | tee -a $LOG_FILE
}

# Check if running as root
if [ "$(id -u)" -ne 0 ]; then
    log "WARNING: This script should be run as root to access all logs"
fi

# System information
log -e "\n=== System Information ==="
log "Hostname: $(hostname)"
log "Kernel version: $(uname -r)"
log "Uptime: $(uptime)"
log "Memory usage:"
free -h | tee -a $LOG_FILE
log "Disk usage:"
df -h / | tee -a $LOG_FILE

# Check environment variables
log -e "\n=== Checking environment variables ==="
log "DJANGO_SETTINGS_MODULE: $DJANGO_SETTINGS_MODULE"
log "ENVIRONMENT: $ENVIRONMENT"
log "AWS_DB_NAME: $AWS_DB_NAME"
log "AWS_DB_USER: $AWS_DB_USER"
log "AWS_DB_HOST: $AWS_DB_HOST"
log "AWS_DB_PORT: $AWS_DB_PORT"
log "AWS_DB_SSL_MODE: $AWS_DB_SSL_MODE"

# Check if database variables are set
if [ -z "$AWS_DB_NAME" ] || [ -z "$AWS_DB_USER" ] || [ -z "$AWS_DB_HOST" ]; then
    log "WARNING: Database environment variables are not properly set!"
fi

# Check processes
log -e "\n=== Running Processes ==="
log "Python processes:"
ps aux | grep python | grep -v grep | tee -a $LOG_FILE
log "Web server processes:"
ps aux | grep -E '(nginx|apache|gunicorn|uwsgi)' | grep -v grep | tee -a $LOG_FILE

# Check network connections
log -e "\n=== Network Connections ==="
log "Active connections:"
netstat -tuln | tee -a $LOG_FILE

# Test database connectivity directly
log -e "\n=== Direct Database Connectivity Test ==="
if [ ! -z "$AWS_DB_HOST" ] && [ ! -z "$AWS_DB_PORT" ]; then
    log "Testing connection to $AWS_DB_HOST:$AWS_DB_PORT..."
    timeout 5 bash -c "< /dev/tcp/$AWS_DB_HOST/$AWS_DB_PORT" 2>/dev/null
    if [ $? -eq 0 ]; then
        log "TCP connection to database successful!"
    else
        log "TCP connection to database FAILED!"
    fi
else
    log "Cannot test database connection - host or port not defined"
fi

# Check application logs
log -e "\n=== Application Logs ==="
LOG_FILES=(/var/log/eb-*log /var/log/app/*.log /var/log/nginx/*log /var/log/eb-docker/containers/eb-current-app/*.log)
for log_file in "${LOG_FILES[@]}"; do
    if ls $log_file 1> /dev/null 2>&1; then
        for file in $log_file; do
            if [ -f "$file" ]; then
                log -e "\n--- Last 50 lines of $file ---"
                tail -n 50 "$file" | tee -a $LOG_FILE
                
                # Check for specific errors
                log -e "\n--- Error analysis in $file ---"
                ERROR_PATTERNS="(Error|ERROR|Exception|CRITICAL|failed|Failed|ConnectionRefused|timeout|Timeout)"
                grep -E "$ERROR_PATTERNS" "$file" | tail -n 20 | tee -a $LOG_FILE
            fi
        done
    fi
done

# Check database connectivity using Django
log -e "\n=== Testing Database Connection via Django ==="
APP_DIR="/var/app/current"
if [ -d "$APP_DIR" ]; then
    cd $APP_DIR
    if [ -d "/var/app/venv" ]; then
        log "Activating virtual environment..."
        source /var/app/venv/*/bin/activate
        
        log "Checking Django version:"
        python -m django --version | tee -a $LOG_FILE
        
        log "Running Django check:"
        python manage.py check --database default | tee -a $LOG_FILE
        
        log "Testing database connection:"
        python manage.py check_db_connection --verbose | tee -a $LOG_FILE
        
        log "Checking health endpoint directly:"
        python -c "
import sys, os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', os.environ.get('DJANGO_SETTINGS_MODULE', 'core.settings'))
django.setup()
from bingo.health import health_check
from django.http import HttpRequest
request = HttpRequest()
print(health_check(request).content.decode('utf-8'))
" | tee -a $LOG_FILE
    else
        log "Virtual environment not found at /var/app/venv"
    fi
else
    log "Application directory not found at $APP_DIR"
fi

log -e "\n=== Diagnosis Complete ==="
log "Full diagnosis log available at: $LOG_FILE"
log "If you're having issues, check the complete logs with:"
log "eb logs bingo-production"
