#!/bin/bash

echo "=== Elastic Beanstalk Environment Diagnostic Tool ==="
echo "Running diagnostics at $(date)"

# Check if running as root
if [ "$(id -u)" -ne 0 ]; then
    echo "WARNING: This script should be run as root to access all logs"
fi

# Check environment variables
echo -e "\n=== Checking environment variables ==="
echo "DJANGO_SETTINGS_MODULE: $DJANGO_SETTINGS_MODULE"
echo "ENVIRONMENT: $ENVIRONMENT"
echo "AWS_DB_NAME: $AWS_DB_NAME"
echo "AWS_DB_USER: $AWS_DB_USER"
echo "AWS_DB_HOST: $AWS_DB_HOST"
echo "AWS_DB_PORT: $AWS_DB_PORT"
echo "AWS_DB_SSL_MODE: $AWS_DB_SSL_MODE"

# Check if database variables are set
if [ -z "$AWS_DB_NAME" ] || [ -z "$AWS_DB_USER" ] || [ -z "$AWS_DB_HOST" ]; then
    echo "WARNING: Database environment variables are not properly set!"
fi

# Check application logs
echo -e "\n=== Application Logs ==="
LOG_FILES=(/var/log/eb-*log /var/log/app/*.log /var/log/nginx/*log)
for log in "${LOG_FILES[@]}"; do
    if [ -f "$log" ]; then
        echo -e "\n--- Last 30 lines of $log ---"
        tail -n 30 "$log"
    fi
done

# Check Python processes
echo -e "\n=== Running Python Processes ==="
ps aux | grep python | grep -v grep

# Check database connectivity using Django
echo -e "\n=== Testing Database Connection ==="
cd /var/app/current
source /var/app/venv/*/bin/activate
python manage.py check_db_connection --verbose

echo -e "\n=== Diagnosis Complete ==="
echo "If you're having issues, check the complete logs with:"
echo "eb logs bingo-production"
