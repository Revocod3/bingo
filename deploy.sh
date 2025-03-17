#!/bin/bash

# Exit on error
set -e

echo "Starting deployment process for Bingo API..."

# Check if environment exists
eb status bingo-production > /dev/null 2>&1
if [ $? -eq 0 ]; then
    # Environment exists, check its status
    STATUS=$(eb status bingo-production | grep "Status:" | awk '{print $2}')
    echo "Environment status: $STATUS"
    
    if [ "$STATUS" != "Ready" ]; then
        echo "Environment is not ready. Current status: $STATUS"
        read -p "Do you want to rebuild the environment? (y/n) " choice
        case "$choice" in
          y|Y ) eb rebuild bingo-production;;
          * ) echo "Please wait until environment is Ready or terminate and create a new one."
              echo "To terminate: eb terminate bingo-production"
              echo "To create new: eb create bingo-production"
              exit 1;;
        esac
    else
        # Environment is ready, deploy
        echo "Deploying to existing environment..."
        eb deploy bingo-production
    fi
else
    # Environment doesn't exist, create it
    echo "Creating new environment..."
    eb create bingo-production
fi

echo "Deployment process completed."
