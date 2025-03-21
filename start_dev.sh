#!/bin/bash

# Check if Redis is running
if ! pgrep redis-server > /dev/null; then
    echo "Starting Redis server..."
    redis-server &
    REDIS_PID=$!
    sleep 2  # Give Redis time to start
else
    echo "Redis server is already running"
fi

# Test Redis connection
echo "Testing Redis connection..."
python test_redis.py

# Check Django WebSocket configuration
echo "Checking WebSocket configuration..."
python manage.py check_websocket

# Start Django development server
echo "Starting Django development server..."
python manage.py runserver

# When Ctrl+C is pressed, clean up
trap 'echo "Shutting down..."; 
      [[ -n "$REDIS_PID" ]] && kill $REDIS_PID; 
      echo "Done"' INT TERM

# Make the script executable
chmod +x start_dev.sh
