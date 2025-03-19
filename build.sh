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

# Print Django version and settings module for debugging
echo "Django version: $(python -m django --version)"
echo "Using settings: $DJANGO_SETTINGS_MODULE"

# Show pending migrations before applying them
echo "Checking for pending migrations..."
python manage.py showmigrations

# Apply database migrations with more verbosity
echo "Applying migrations..."
python manage.py migrate --noinput --verbosity=2

# Verify migrations were applied
echo "Verifying migrations..."
python manage.py showmigrations | grep -v '\[ \]'

# Collect static files 
python manage.py collectstatic --noinput --verbosity=2

echo "Build completed successfully!"
