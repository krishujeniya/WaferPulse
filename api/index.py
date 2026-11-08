"""Vercel Serverless Function Entry Point."""

import sys
from pathlib import Path

# Add project root to sys.path for serverless execution environment
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from backend.app.main import app

# Export ASGI application for Vercel
__all__ = ["app"]
