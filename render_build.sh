#!/usr/bin/env bash
# exit on error
set -o errexit

# Install dependencies
pip install -r requirements.txt

# Apply migrations
python manage.py migrate

# Collect static files (if needed)
python manage.py collectstatic --no-input
