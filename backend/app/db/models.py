"""SQLAlchemy ORM Entities for MLOps SaaS Operations."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import JSON, Boolean, Column, DateTime, Float, Integer, String, Text

from backend.app.db.database import Base


def utc_now():
    return datetime.now(UTC)


class DatasetModel(Base):
    """Uploaded or ingested wafer sensor dataset records."""

    __tablename__ = "datasets"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), unique=True, index=True, nullable=False)
    file_type = Column(String(50), nullable=False)  # "training" or "prediction"
    row_count = Column(Integer, default=0)
    column_count = Column(Integer, default=0)
    is_valid = Column(Boolean, default=True)
    validation_report = Column(JSON, default=dict)
    file_path = Column(String(500), nullable=False)
    created_at = Column(DateTime, default=utc_now)


class TrainingJobModel(Base):
    """Asynchronous training pipeline execution record."""

    __tablename__ = "training_jobs"

    id = Column(String(100), primary_key=True, index=True)
    status = Column(String(50), default="queued")  # queued, running, completed, failed
    current_step = Column(String(100), default="Initialized")
    progress_pct = Column(Integer, default=0)
    model_version = Column(String(100), nullable=True)
    dataset_name = Column(String(255), nullable=True)
    total_wafers = Column(Integer, default=0)
    features_retained = Column(Integer, default=0)
    clusters_count = Column(Integer, default=0)
    metrics = Column(JSON, default=dict)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now)
    completed_at = Column(DateTime, nullable=True)


class InferenceJobModel(Base):
    """Batch inference execution record."""

    __tablename__ = "inference_jobs"

    id = Column(String(100), primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    model_version = Column(String(100), nullable=False)
    total_wafers = Column(Integer, default=0)
    defects_count = Column(Integer, default=0)
    yield_rate = Column(Float, default=100.0)
    results = Column(JSON, default=list)  # list of top predictions and diagnoses
    created_at = Column(DateTime, default=utc_now)


class SensorAlertModel(Base):
    """Sensor deviation and drift alert events."""

    __tablename__ = "sensor_alerts"

    id = Column(Integer, primary_key=True, index=True)
    sensor_name = Column(String(50), nullable=False, index=True)
    chamber_id = Column(String(50), nullable=True)
    severity = Column(String(20), nullable=False)  # WARNING, CRITICAL
    z_score = Column(Float, nullable=False)
    message = Column(String(500), nullable=False)
    created_at = Column(DateTime, default=utc_now)
