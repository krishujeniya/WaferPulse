"""Training API Schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class TrainTriggerRequest(BaseModel):
    data_dir: str | None = Field("Training_Batch_Files", description="Relative batch folder")
    version: str | None = Field(None, description="Explicit model version name")
    set_active: bool = Field(True, description="Whether to promote to active production model")


class TrainingJobStatus(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    status: str
    current_step: str
    progress_pct: int
    model_version: str | None = None
    total_wafers: int = 0
    features_retained: int = 0
    clusters_count: int = 0
    metrics: dict[str, Any] = Field(default_factory=dict)
    error_message: str | None = None
    created_at: datetime
    completed_at: datetime | None = None
