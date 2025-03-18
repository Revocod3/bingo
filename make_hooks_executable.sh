#!/bin/bash

echo "Making hooks executable..."

# Make predeploy hooks executable
if [ -d ".platform/hooks/predeploy" ]; then
    chmod +x .platform/hooks/predeploy/*.sh
    echo "Made predeploy hooks executable"
fi

# Make postdeploy hooks executable
if [ -d ".platform/hooks/postdeploy" ]; then
    chmod +x .platform/hooks/postdeploy/*.sh
    echo "Made postdeploy hooks executable"
fi

# Make .ebextensions scripts executable
find .ebextensions -name "*.py" -exec chmod +x {} \;
echo "Made .ebextensions scripts executable"

echo "All hooks are now executable!"
