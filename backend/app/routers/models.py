"""Model Registry and Version Management Endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from backend.app.config import MODELS_DIR
from backend.app.schemas.model import ModelCard, PromoteModelRequest
from src.models.registry import ModelRegistry

router = APIRouter(prefix="/models", tags=["Models"])


@router.get("", response_model=list[ModelCard])
def list_models():
    """List all registered models and evaluation metric cards."""
    registry = ModelRegistry(registry_dir=MODELS_DIR)
    models = registry.list_models()
    return models


@router.get("/active", response_model=ModelCard)
def get_active_model():
    """Retrieve the active production model metadata."""
    registry = ModelRegistry(registry_dir=MODELS_DIR)
    active_v = registry.get_active_version()
    if not active_v:
        raise HTTPException(status_code=404, detail="No active model found in registry.")

    models = registry.list_models()
    for m in models:
        if m.get("version") == active_v:
            return m

    raise HTTPException(status_code=404, detail="Active model metadata not found.")


@router.post("/promote")
def promote_model(payload: PromoteModelRequest):
    """Promote a registered model version to active production state."""
    registry = ModelRegistry(registry_dir=MODELS_DIR)
    try:
        registry.set_active_version(payload.version)
        return {"status": "promoted", "active_version": payload.version}
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/rollback")
def rollback_model():
    """Roll back to previous active model version."""
    registry = ModelRegistry(registry_dir=MODELS_DIR)
    previous_v = registry.rollback()
    if not previous_v:
        raise HTTPException(
            status_code=400, detail="No previous model version available for rollback."
        )
    return {"status": "rolled_back", "active_version": previous_v}
