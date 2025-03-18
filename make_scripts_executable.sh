#!/bin/bash

echo "Making deployment scripts executable..."

# Make hook scripts executable
if [ -d ".platform/hooks/postdeploy" ]; then
    chmod +x .platform/hooks/postdeploy/*.sh
    echo "Made postdeploy hooks executable"
fi

if [ -d ".platform/hooks/predeploy" ]; then
    chmod +x .platform/hooks/predeploy/*.sh
    echo "Made predeploy hooks executable"
fi

chmod +x .ebextensions/check_requirements.py
echo "Made check_requirements.py executable"

chmod +x ebdiagnose.sh
echo "Made ebdiagnose.sh executable"

chmod +x deployment_test.py  
echo "Made deployment_test.py executable"

echo "All scripts are now executable!"
