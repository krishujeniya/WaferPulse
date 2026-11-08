"""Inference and Root-Cause API Schemas."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class SinglePredictionRequest(BaseModel):
    wafer_id: str | None = Field(None, description="Wafer barcode or identifier")
    sensors: dict[str, float] = Field(..., description="Mapping of Sensor_1...Sensor_N to float values")
    model_version: str | None = Field(None, description="Target model version or active by default")


class SensorAnomalyDetail(BaseModel):
    sensor: str
    value: float
    baseline_mean: float
    baseline_std: float
    z_score: float
    direction: str
    severity: str


class SinglePredictionResponse(BaseModel):
    wafer_id: str
    cluster_id: int
    prediction: str  # "Pass" or "Defect"
    is_defective: bool
    defect_probability: float
    model_version: str
    top_anomalies: list[SensorAnomalyDetail]


class BatchInferenceResponse(BaseModel):
    job_id: str
    model_version: str
    total_wafers: int
    defects_count: int
    yield_rate: float
    results: list[dict[str, Any]]
