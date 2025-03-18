#!/usr/bin/env bash
# exit on error
set -o errexit

# Install system dependencies
apt-get update
apt-get install -y --no-install-recommends gcc python3-dev

# Install Python dependencies
pip install -r requirements.txt

# Create static directory if it doesn't exist
mkdir -p static

# Apply database migrations
python manage.py migrate

# Collect static files with more verbosity for debugging
python manage.py collectstatic --noinput --verbosity=2

# Additional build steps can go here
echo "Build completed successfully!"
