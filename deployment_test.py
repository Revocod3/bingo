#!/usr/bin/env python3
"""
Simple script to test deployments without relying on the full application.
This is useful for initial deployment troubleshooting.
"""
import os
import sys
import socket
import platform
import json

def main():
    """Generate a simple report on the deployment environment"""
    report = {
        "success": True,
        "hostname": socket.gethostname(),
        "platform": {
            "system": platform.system(),
            "release": platform.release(), 
            "version": platform.version(),
            "python_version": sys.version
        },
        "environment_variables": {
            key: value for key, value in os.environ.items() 
            if not any(secret in key.lower() for secret in ['password', 'secret', 'key'])
        },
        "working_directory": os.getcwd(),
        "files": os.listdir()
    }
    
    print(json.dumps(report, indent=2))
    return 0

if __name__ == "__main__":
    sys.exit(main())
