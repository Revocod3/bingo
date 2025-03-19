#!/usr/bin/env bash
# Script for building the application on Render.com with better migration handling
set -o errexit

echo "Running render_build.sh..."

# Install dependencies
pip install -r requirements.txt

# Create static directory if it doesn't exist
mkdir -p static

# Update database schema
echo "Checking database connection..."
python manage.py check_db_connection --verbose

echo "Checking current state of migrations..."
python manage.py showmigrations

# Run migrations with verbosity for debugging
echo "Applying database migrations..."
python manage.py migrate --noinput --verbosity=2

# Verify migrations were successful
echo "Verifying migrations were applied..."
python manage.py check_migrations

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Output useful info
echo "Build process completed."
