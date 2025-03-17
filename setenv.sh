#!/bin/bash

# This script sets required environment variables in Elastic Beanstalk

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
eb status $ENVIRONMENT > /dev/null 2>&1
if [ $? -ne 0 ]; then
  echo "Error: Environment '$ENVIRONMENT' does not exist"
  exit 1
fi

# Load variables from .env file if it exists
if [ -f .env ]; then
  echo "Loading variables from .env file..."
  source .env
else
  echo "No .env file found. Please provide values when prompted."
fi

# Set database variables
if [ -z "$AWS_DB_NAME" ]; then
  read -p "Enter AWS_DB_NAME: " AWS_DB_NAME
fi

if [ -z "$AWS_DB_USER" ]; then
  read -p "Enter AWS_DB_USER: " AWS_DB_USER
fi

if [ -z "$AWS_DB_PASSWORD" ]; then
  read -p "Enter AWS_DB_PASSWORD: " AWS_DB_PASSWORD
fi

if [ -z "$AWS_DB_HOST" ]; then
  read -p "Enter AWS_DB_HOST: " AWS_DB_HOST
fi

if [ -z "$AWS_DB_PORT" ]; then
  AWS_DB_PORT="5432"
  echo "Using default AWS_DB_PORT: $AWS_DB_PORT"
fi

# Set email variables
if [ -z "$EMAIL_HOST" ]; then
  EMAIL_HOST="smtp.gmail.com"
  echo "Using default EMAIL_HOST: $EMAIL_HOST"
fi

if [ -z "$EMAIL_PORT" ]; then
  EMAIL_PORT="587"
  echo "Using default EMAIL_PORT: $EMAIL_PORT"
fi

if [ -z "$EMAIL_HOST_USER" ]; then
  read -p "Enter EMAIL_HOST_USER: " EMAIL_HOST_USER
fi

if [ -z "$EMAIL_HOST_PASSWORD" ]; then
  read -p "Enter EMAIL_HOST_PASSWORD: " EMAIL_HOST_PASSWORD
fi

if [ -z "$DEFAULT_FROM_EMAIL" ]; then
  DEFAULT_FROM_EMAIL=$EMAIL_HOST_USER
  echo "Using EMAIL_HOST_USER as DEFAULT_FROM_EMAIL: $DEFAULT_FROM_EMAIL"
fi

# Set other required variables
if [ -z "$SECRET_KEY" ]; then
  SECRET_KEY=$(python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')
  echo "Generated new SECRET_KEY"
fi

if [ -z "$FRONTEND_URL" ]; then
  read -p "Enter FRONTEND_URL: " FRONTEND_URL
fi

# Set the environment variables in Elastic Beanstalk
echo "Setting environment variables in $ENVIRONMENT..."
eb setenv \
  SECRET_KEY="$SECRET_KEY" \
  AWS_DB_NAME="$AWS_DB_NAME" \
  AWS_DB_USER="$AWS_DB_USER" \
  AWS_DB_PASSWORD="$AWS_DB_PASSWORD" \
  AWS_DB_HOST="$AWS_DB_HOST" \
  AWS_DB_PORT="$AWS_DB_PORT" \
  AWS_DB_SSL_MODE="require" \
  EMAIL_HOST="$EMAIL_HOST" \
  EMAIL_PORT="$EMAIL_PORT" \
  EMAIL_HOST_USER="$EMAIL_HOST_USER" \
  EMAIL_HOST_PASSWORD="$EMAIL_HOST_PASSWORD" \
  EMAIL_USE_TLS="True" \
  DEFAULT_FROM_EMAIL="$DEFAULT_FROM_EMAIL" \
  BYPASS_EMAIL_VERIFICATION="False" \
  EMAIL_BACKEND="django.core.mail.backends.smtp.EmailBackend" \
  FRONTEND_URL="$FRONTEND_URL" \
  ENVIRONMENT="production" \
  DJANGO_SETTINGS_MODULE="core.settings"

echo "Environment variables set successfully!"
echo "To verify, run: eb printenv $ENVIRONMENT"
