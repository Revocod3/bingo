#!/usr/bin/env bash
# exit on error
set -o errexit

# Install system dependencies
apt-get update
apt-get install -y --no-install-recommends gcc python3-dev

# Install Python dependencies
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --no-input

# Apply database migrations
python manage.py migrate
