#!/usr/bin/env python3
"""
Cache Manager Script

Convenience script to run the cache and performance management CLI.
"""

import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.cli.cache_manager_cli import main

if __name__ == "__main__":
    sys.exit(main())
