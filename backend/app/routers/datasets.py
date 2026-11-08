"""Dataset Management and Ingestion Endpoints."""

from __future__ import annotations

import shutil
from pathlib import Path

import pandas as pd
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from backend.app.config import PREDICTION_BATCHES_DIR, TRAINING_BATCHES_DIR
from backend.app.db.database import get_db
from backend.app.db.models import DatasetModel
from backend.app.schemas.dataset import DatasetPreview, DatasetResponse
from src.data.generator import generate_batch_files
from src.data.validator import TelemetryValidator

router = APIRouter(prefix="/datasets", tags=["Datasets"])


@router.get("", response_model=list[DatasetResponse])
def list_datasets(
    file_type: str | None = Query(None, description="training or prediction"),
    db: Session = Depends(get_db),
):
    """List all ingested sensor datasets with schema validation reports."""
    # Synchronize database with files on disk if table is empty
    existing_count = db.query(DatasetModel).count()
    if existing_count == 0:
        _scan_and_sync_disk_datasets(db)

    query = db.query(DatasetModel)
    if file_type:
        query = query.filter(DatasetModel.file_type == file_type)
    return query.order_by(DatasetModel.created_at.desc()).all()


@router.post("/upload", response_model=DatasetResponse)
async def upload_dataset(
    file: UploadFile = File(...),
    file_type: str = Query("training", pattern="^(training|prediction)$"),
    db: Session = Depends(get_db),
):
    """Upload and validate a new wafer telemetry CSV batch."""
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported.")

    dest_dir = TRAINING_BATCHES_DIR if file_type == "training" else PREDICTION_BATCHES_DIR
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_path = dest_dir / file.filename

    with open(dest_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Validate against schema
    validator = TelemetryValidator()
    report = validator.validate_file(
        dest_path,
        is_training=(file_type == "training"),
        quarantine_dir=dest_dir / "quarantine",
    )

    # Save to database
    record = db.query(DatasetModel).filter(DatasetModel.filename == file.filename).first()
    if not record:
        record = DatasetModel(
            filename=file.filename,
            file_type=file_type,
            file_path=str(dest_path),
        )
        db.add(record)

    record.row_count = report.row_count
    record.column_count = report.column_count
    record.is_valid = report.is_valid
    record.validation_report = report.to_dict()
    db.commit()
    db.refresh(record)

    return record


@router.post("/generate-sample", response_model=list[DatasetResponse])
def generate_sample_batches(
    file_type: str = Query("training", pattern="^(training|prediction)$"),
    batch_count: int = Query(2, ge=1, le=5),
    samples_per_batch: int = Query(100, ge=20, le=500),
    db: Session = Depends(get_db),
):
    """Generate physically grounded synthetic wafer batches for testing."""
    target_dir = TRAINING_BATCHES_DIR if file_type == "training" else PREDICTION_BATCHES_DIR
    generated_paths = generate_batch_files(
        output_dir=target_dir,
        num_files=batch_count,
        samples_per_file=samples_per_batch,
        num_sensors=60,
        is_training=(file_type == "training"),
    )

    validator = TelemetryValidator()
    results = []

    for path in generated_paths:
        report = validator.validate_file(path, is_training=(file_type == "training"))
        rec = db.query(DatasetModel).filter(DatasetModel.filename == path.name).first()
        if not rec:
            rec = DatasetModel(
                filename=path.name,
                file_type=file_type,
                file_path=str(path),
            )
            db.add(rec)
        rec.row_count = report.row_count
        rec.column_count = report.column_count
        rec.is_valid = report.is_valid
        rec.validation_report = report.to_dict()
        db.commit()
        db.refresh(rec)
        results.append(rec)

    return results


@router.get("/{filename}/preview", response_model=DatasetPreview)
def preview_dataset(filename: str, db: Session = Depends(get_db)):
    """Retrieve row preview and summary statistics for a dataset."""
    record = db.query(DatasetModel).filter(DatasetModel.filename == filename).first()
    if not record or not Path(record.file_path).exists():
        raise HTTPException(status_code=404, detail="Dataset not found")

    df = pd.read_csv(record.file_path)
    preview_df = df.head(10).fillna(0.0)

    numeric_cols = df.select_dtypes(include="number").columns[:15]
    stats = {}
    for col in numeric_cols:
        series = df[col].dropna()
        if not series.empty:
            stats[col] = {
                "mean": round(float(series.mean()), 2),
                "std": round(float(series.std()), 2),
                "min": round(float(series.min()), 2),
                "max": round(float(series.max()), 2),
            }

    return DatasetPreview(
        filename=filename,
        row_count=len(df),
        column_count=len(df.columns),
        columns=list(df.columns),
        preview_rows=preview_df.to_dict(orient="records"),
        statistics=stats,
    )


def _scan_and_sync_disk_datasets(db: Session):
    """Helper to register files existing on disk into database."""
    validator = TelemetryValidator()
    for dir_path, f_type in [
        (TRAINING_BATCHES_DIR, "training"),
        (PREDICTION_BATCHES_DIR, "prediction"),
    ]:
        for csv_f in dir_path.glob("*.csv"):
            report = validator.validate_file(csv_f, is_training=(f_type == "training"))
            rec = DatasetModel(
                filename=csv_f.name,
                file_type=f_type,
                file_path=str(csv_f),
                row_count=report.row_count,
                column_count=report.column_count,
                is_valid=report.is_valid,
                validation_report=report.to_dict(),
            )
            db.add(rec)
    db.commit()
