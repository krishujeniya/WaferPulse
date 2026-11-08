"""Fab Health, Drift Monitoring, and Telemetry Endpoints."""

from __future__ import annotations

import pandas as pd
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.config import MODELS_DIR, PREDICTION_BATCHES_DIR, TRAINING_BATCHES_DIR
from backend.app.db.database import get_db
from backend.app.db.models import SensorAlertModel
from backend.app.schemas.monitoring import (
    ChamberHealthItem,
    DriftSummaryResponse,
    FabOverviewResponse,
    SensorDriftItem,
)
from src.data.generator import generate_batch_files
from src.models.registry import ModelRegistry
from src.monitoring.drift import assess_sensor_drift

router = APIRouter(prefix="/monitoring", tags=["Monitoring"])


@router.get("/drift", response_model=DriftSummaryResponse)
def get_sensor_drift_report():
    """Calculate Population Stability Index (PSI) and Kolmogorov-Smirnov drift statistics."""
    # Load baseline from Training_Batch_Files or in-memory fallback
    base_df = None
    try:
        TRAINING_BATCHES_DIR.mkdir(parents=True, exist_ok=True)
        train_files = list(TRAINING_BATCHES_DIR.glob("*.csv"))
        if not train_files:
            train_files = generate_batch_files(TRAINING_BATCHES_DIR, num_files=2, is_training=True)
        if train_files:
            base_df = pd.concat([pd.read_csv(f) for f in train_files[:3]], ignore_index=True)
    except Exception:
        pass

    if base_df is None or base_df.empty:
        from src.data.generator import generate_wafer_telemetry
        base_df = generate_wafer_telemetry(num_samples=250, is_training=True, random_state=42)

    # Load current from Prediction_Batch_files or in-memory fallback
    curr_df = None
    try:
        PREDICTION_BATCHES_DIR.mkdir(parents=True, exist_ok=True)
        pred_files = list(PREDICTION_BATCHES_DIR.glob("*.csv"))
        if not pred_files:
            pred_files = generate_batch_files(
                PREDICTION_BATCHES_DIR, num_files=1, is_training=False, random_state_start=999
            )
        if pred_files:
            curr_df = pd.concat([pd.read_csv(f) for f in pred_files[:3]], ignore_index=True)
    except Exception:
        pass

    if curr_df is None or curr_df.empty:
        from src.data.generator import generate_wafer_telemetry
        curr_df = generate_wafer_telemetry(num_samples=180, is_training=False, random_state=999)

    summary = assess_sensor_drift(baseline_df=base_df, current_df=curr_df)

    return DriftSummaryResponse(
        total_sensors_monitored=summary.total_sensors_monitored,
        stable_count=summary.stable_count,
        moderate_drift_count=summary.moderate_drift_count,
        critical_drift_count=summary.critical_drift_count,
        overall_status=summary.overall_status,
        top_drifted_sensors=[
            SensorDriftItem(
                sensor=s.sensor,
                psi=s.psi,
                ks_statistic=s.ks_statistic,
                ks_p_value=s.ks_p_value,
                status=s.status,
                baseline_mean=s.baseline_mean,
                current_mean=s.current_mean,
                mean_shift_percent=s.mean_shift_percent,
            )
            for s in summary.top_drifted_sensors
        ],
    )


@router.get("/fab-overview", response_model=FabOverviewResponse)
def get_fab_overview(db: Session = Depends(get_db)):
    """Comprehensive industrial fab monitoring status across chambers."""
    registry = ModelRegistry(registry_dir=MODELS_DIR)
    active_v = registry.get_active_version()

    drift_report = get_sensor_drift_report()

    chambers = [
        ChamberHealthItem(
            chamber_id="Chamber_A",
            status="OPTIMAL",
            yield_rate=98.4,
            wafers_processed=1420,
            active_recipe="CMP-Copper-P4",
            rf_power_kw=13.56,
            pressure_mtorr=15.1,
            temp_celsius=64.8,
        ),
        ChamberHealthItem(
            chamber_id="Chamber_B",
            status="OPTIMAL",
            yield_rate=97.1,
            wafers_processed=1190,
            active_recipe="EUV-Litho-Fine-7nm",
            rf_power_kw=13.58,
            pressure_mtorr=14.9,
            temp_celsius=65.2,
        ),
        ChamberHealthItem(
            chamber_id="Chamber_C",
            status="WARNING" if drift_report.critical_drift_count > 0 else "OPTIMAL",
            yield_rate=92.3,
            wafers_processed=980,
            active_recipe="Plasma-Etch-CF4",
            rf_power_kw=14.12,
            pressure_mtorr=16.8,
            temp_celsius=68.5,
        ),
    ]

    total_processed = sum(c.wafers_processed for c in chambers)
    avg_yield = round(sum(c.yield_rate * c.wafers_processed for c in chambers) / total_processed, 2)

    return FabOverviewResponse(
        system_status="ONLINE",
        active_model_version=active_v,
        total_wafers_processed=total_processed,
        overall_yield_rate=avg_yield,
        active_alarms_count=drift_report.critical_drift_count,
        chambers=chambers,
        recent_drift=drift_report,
    )


@router.get("/alerts")
def list_alerts(db: Session = Depends(get_db)):
    """Retrieve recent sensor alarms."""
    return db.query(SensorAlertModel).order_by(SensorAlertModel.created_at.desc()).limit(20).all()
