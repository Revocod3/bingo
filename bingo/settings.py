"""
Django settings for bingo project - replaced by core/settings.py.
This file now serves as a redirect to the main settings file.
"""

import os
import sys
from pathlib import Path

# Redirect to the actual settings file
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.settings import *
