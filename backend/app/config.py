"""WaferGuard Application Configuration."""

from __future__ import annotations

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models"
ARTIFACTS_DIR = BASE_DIR / "artifacts"
TRAINING_BATCHES_DIR = DATA_DIR / "raw"
PREDICTION_BATCHES_DIR = DATA_DIR / "prediction"
IS_VERCEL = bool(os.getenv("VERCEL") or os.getenv("AWS_LAMBDA_FUNCTION_NAME"))

if IS_VERCEL:
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:////tmp/waferguard.db")
    REPORTS_DIR = Path("/tmp/reports")
else:
    DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'waferguard.db'}")
    REPORTS_DIR = BASE_DIR / "reports"

# Ensure runtime directories exist where permitted
for p in [
    DATA_DIR,
    DATA_DIR / "raw",
    DATA_DIR / "interim",
    DATA_DIR / "processed",
    DATA_DIR / "prediction",
    DATA_DIR / "quarantine",
    MODELS_DIR,
    ARTIFACTS_DIR,
    REPORTS_DIR,
]:
    try:
        p.mkdir(parents=True, exist_ok=True)
    except OSError:
        pass

CORS_ORIGINS = ["*"]
API_PREFIX = "/api/v1"
