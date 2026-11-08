"""Monitoring and Telemetry API Schemas."""

from __future__ import annotations

from pydantic import BaseModel


class SensorDriftItem(BaseModel):
    sensor: str
    psi: float
    ks_statistic: float
    ks_p_value: float
    status: str
    baseline_mean: float
    current_mean: float
    mean_shift_percent: float


class DriftSummaryResponse(BaseModel):
    total_sensors_monitored: int
    stable_count: int
    moderate_drift_count: int
    critical_drift_count: int
    overall_status: str
    top_drifted_sensors: list[SensorDriftItem]


class ChamberHealthItem(BaseModel):
    chamber_id: str
    status: str  # "OPTIMAL", "WARNING", "DEGRADED"
    yield_rate: float
    wafers_processed: int
    active_recipe: str
    rf_power_kw: float
    pressure_mtorr: float
    temp_celsius: float


class FabOverviewResponse(BaseModel):
    system_status: str
    active_model_version: str | None
    total_wafers_processed: int
    overall_yield_rate: float
    active_alarms_count: int
    chambers: list[ChamberHealthItem]
    recent_drift: DriftSummaryResponse
