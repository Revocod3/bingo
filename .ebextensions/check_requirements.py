#!/usr/bin/env python3
"""
Verifies that all required dependencies are installed correctly.
"""
import sys
import importlib
import pkg_resources

REQUIRED_PACKAGES = [
    'django',
    'djangorestframework',
    'djangorestframework-simplejwt',
    'dj-rest-auth',
    'psycopg2',
    'gunicorn',
    'psutil',
    'drf-yasg',
]

def check_installed_packages():
    """Check if all required packages are installed with their versions"""
    missing = []
    installed = {}
    
    for package in REQUIRED_PACKAGES:
        try:
            module = importlib.import_module(package)
            version = getattr(module, '__version__', 'unknown')
            if version == 'unknown':
                try:
                    version = pkg_resources.get_distribution(package).version
                except:
                    pass
            installed[package] = version
        except ImportError:
            missing.append(package)
    
    print(f"=== Package Check Results ===")
    print(f"Installed packages: {len(installed)}")
    print(f"Missing packages: {len(missing)}")
    
    if missing:
        print("\nMissing packages:")
        for pkg in missing:
            print(f"- {pkg}")
    
    print("\nInstalled package versions:")
    for pkg, version in installed.items():
        print(f"- {pkg}: {version}")
    
    return len(missing) == 0

if __name__ == "__main__":
    success = check_installed_packages()
    sys.exit(0 if success else 1)
