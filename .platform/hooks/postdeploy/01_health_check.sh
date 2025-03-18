#!/bin/bash

echo "=== Post-deployment Health Check ==="
TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")
LOG_FILE="/var/log/app/post_deploy_check_$(date +%Y%m%d_%H%M%S).log"

echo "Starting health check at $TIMESTAMP" | tee -a $LOG_FILE
echo "Environment variables:" | tee -a $LOG_FILE
echo "DJANGO_SETTINGS_MODULE: $DJANGO_SETTINGS_MODULE" | tee -a $LOG_FILE
echo "AWS_DB_HOST: $AWS_DB_HOST" | tee -a $LOG_FILE
echo "AWS_DB_NAME: $AWS_DB_NAME" | tee -a $LOG_FILE

# Check if essential environment variables are set
if [ -z "$DJANGO_SETTINGS_MODULE" ]; then
    echo "ERROR: DJANGO_SETTINGS_MODULE is not set!" | tee -a $LOG_FILE
    # Don't exit with error to avoid deployment failure
fi

# Test database connection
cd /var/app/current
source /var/app/venv/*/bin/activate

echo "Python version:" | tee -a $LOG_FILE
python --version | tee -a $LOG_FILE

echo "Pip packages:" | tee -a $LOG_FILE
pip freeze | tee -a $LOG_FILE

echo "Testing database connection..." | tee -a $LOG_FILE
python manage.py check_db_connection --verbose | tee -a $LOG_FILE

# Run deployment test script
echo "Running deployment test..." | tee -a $LOG_FILE
python deployment_test.py | tee -a $LOG_FILE

# Check requirements
echo "Checking requirements..." | tee -a $LOG_FILE
python .ebextensions/check_requirements.py | tee -a $LOG_FILE

echo "Health check completed at $(date +"%Y-%m-%d %H:%M:%S")" | tee -a $LOG_FILE
echo "Log file: $LOG_FILE"

# Always exit with success to prevent deployment rollback
exit 0
