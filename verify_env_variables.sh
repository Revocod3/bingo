#!/bin/bash

echo "Verifying environment variables in Elastic Beanstalk..."

# Exit on error
set -e

# Check if environment name is provided
if [ -z "$1" ]; then
  ENVIRONMENT="bingo-production"
  echo "Using default environment name: $ENVIRONMENT"
else
  ENVIRONMENT="$1"
  echo "Using provided environment name: $ENVIRONMENT"
fi

# Check if environment exists
eb status $ENVIRONMENT &>/dev/null || { 
  echo "❌ Environment '$ENVIRONMENT' does not exist or eb CLI not configured."
  echo "Try running 'eb init' first or check environment name."
  exit 1
}

# List current environment variables
echo "Current environment variables in $ENVIRONMENT:"
eb printenv $ENVIRONMENT

# Check for critical variables
echo -e "\nChecking critical variables..."
VARS=$(eb printenv $ENVIRONMENT)

CRITICAL_VARS=(
  "DJANGO_SETTINGS_MODULE" 
  "SECRET_KEY" 
  "AWS_DB_NAME" 
  "AWS_DB_USER"
  "AWS_DB_PASSWORD"
  "AWS_DB_HOST"
  "AWS_DB_PORT"
  "ENVIRONMENT"
  "EMAIL_HOST"
  "EMAIL_HOST_USER"
  "EMAIL_HOST_PASSWORD"
  "FRONTEND_URL"
)

MISSING=0
for VAR in "${CRITICAL_VARS[@]}"; do
  if ! echo "$VARS" | grep -q "$VAR: "; then
    echo "⚠️ Missing: $VAR"
    MISSING=$((MISSING+1))
  else
    echo "✓ Found: $VAR"
  fi
done

# Additional validations
if echo "$VARS" | grep -q "AWS_DB_HOST: "; then
  DB_HOST=$(echo "$VARS" | grep "AWS_DB_HOST: " | awk '{print $2}')
  if [[ "$DB_HOST" == *".rds."* ]]; then
    echo "✓ AWS_DB_HOST appears to be a valid RDS endpoint"
  else
    echo "⚠️ Warning: AWS_DB_HOST doesn't look like a standard RDS endpoint"
  fi
fi

if echo "$VARS" | grep -q "EMAIL_HOST: " && echo "$VARS" | grep -q "EMAIL_HOST_USER: "; then
  EMAIL_HOST=$(echo "$VARS" | grep "EMAIL_HOST: " | awk '{print $2}')
  EMAIL_USER=$(echo "$VARS" | grep "EMAIL_HOST_USER: " | awk '{print $2}')
  
  if [[ "$EMAIL_HOST" == "smtp.gmail.com" ]] && [[ "$EMAIL_USER" == *"@gmail.com" ]]; then
    echo "✓ Gmail SMTP configuration appears valid"
  fi
fi

if [ $MISSING -gt 0 ]; then
  echo -e "\n⚠️ ALERT: $MISSING critical variables are missing!"
  echo "Consider setting them using: ./setenv.sh $ENVIRONMENT"
else
  echo -e "\n✓ All critical variables are set."
fi

# Attempt to test connectivity
echo -e "\nTesting connectivity..."

# Test if we can access the environment
echo "Checking if environment is accessible..."
EB_STATUS=$(eb status $ENVIRONMENT 2>&1)
if echo "$EB_STATUS" | grep -q "Status: Ready"; then
  echo "✓ Environment is accessible and Ready"
else
  echo "⚠️ Environment may not be in Ready state:"
  echo "$EB_STATUS" | grep "Status:"
fi

echo "Environment verification completed."

# Return appropriate exit code
if [ $MISSING -gt 0 ]; then
  exit 1
else
  exit 0
fi
