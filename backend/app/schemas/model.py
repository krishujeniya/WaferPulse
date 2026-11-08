"""Model Registry API Schemas."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class ModelCard(BaseModel):
    version: str
    created_at: str
    status: str
    is_active: bool
    dataset_name: str | None = None
    features_count: int
    feature_columns: list[str]
    clusters_count: int
    metrics: dict[str, Any]
    dropped_high_null: list[str]
    dropped_zero_var: list[str]


class PromoteModelRequest(BaseModel):
    version: str
