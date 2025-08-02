#!/usr/bin/env python3
"""
Helper script to get the correct Python executable path.
"""

import os
import sys
from pathlib import Path


def get_python_executable():
    """Get the Python executable path, preferring virtual environment."""
    # Check for virtual environment
    venv_paths = [
        ".venv/Scripts/python.exe",  # Windows
        ".venv/bin/python",          # Linux/Mac
        "venv/Scripts/python.exe",   # Windows (alternative)
        "venv/bin/python",           # Linux/Mac (alternative)
    ]
    
    for venv_path in venv_paths:
        if os.path.exists(venv_path):
            return venv_path
    
    # Fallback to system Python
    return sys.executable


def main():
    """Print the Python executable path."""
    python_path = get_python_executable()
    print(python_path)


if __name__ == "__main__":
    main() 