#!/usr/bin/env python3
"""Entrypoint for HyperUnlock-8G3."""
import sys
from pathlib import Path

# Ensure root package directory is in sys.path
sys.path.insert(0, str(Path(__file__).parent))

from hyperunlock.cli import main

if __name__ == "__main__":
    main()
