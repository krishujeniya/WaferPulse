"""Dataset API Schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class DatasetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    file_type: str
    row_count: int
    column_count: int
    is_valid: bool
    validation_report: dict[str, Any]
    created_at: datetime


class DatasetPreview(BaseModel):
    filename: str
    row_count: int
    column_count: int
    columns: list[str]
    preview_rows: list[dict[str, Any]]
    statistics: dict[str, dict[str, float]]
