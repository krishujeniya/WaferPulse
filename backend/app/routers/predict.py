"""Inference and Root-Cause Diagnosis Endpoints."""

from __future__ import annotations

import shutil
import uuid
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from backend.app.config import MODELS_DIR, REPORTS_DIR
from backend.app.db.database import get_db
from backend.app.db.models import InferenceJobModel
from backend.app.schemas.prediction import (
    BatchInferenceResponse,
    SensorAnomalyDetail,
    SinglePredictionRequest,
    SinglePredictionResponse,
)
from src.explain.root_cause import diagnose_single_wafer
from src.models.predict_model import run_batch_inference
from src.models.registry import ModelRegistry

router = APIRouter(prefix="/predict", tags=["Inference"])


@router.post("/single", response_model=SinglePredictionResponse)
def predict_single_wafer(payload: SinglePredictionRequest):
    """Predict defect probability and diagnose root cause for a single wafer reading."""
    registry = ModelRegistry(registry_dir=MODELS_DIR)
    try:
        bundle = registry.load_bundle(version=payload.model_version)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

    wafer_id = payload.wafer_id or f"Wafer_Live_{uuid.uuid4().hex[:6]}"

    # Build single-row DataFrame
    row_data = {"Wafer": [wafer_id]}
    for col in bundle.preprocessor.feature_columns:
        row_data[col] = [payload.sensors.get(col, np.nan)]
    df = pd.DataFrame(row_data)

    try:
        X, _, _ = bundle.preprocessor.transform(df)
        cluster = int(bundle.clusterer.predict(X)[0])
        preds, probs = bundle.ensemble.predict(X, np.array([cluster]))
        is_defective = bool(preds[0] == 1)
        prob = float(probs[0])
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Inference computation error: {e!s}")

    # Diagnose root cause
    diagnosis = diagnose_single_wafer(
        wafer_id=wafer_id,
        sensor_values=payload.sensors,
        baseline_stats=bundle.preprocessor.baseline_stats,
        defect_prob=prob,
        cluster_id=cluster,
        top_k=5,
    )

    return SinglePredictionResponse(
        wafer_id=wafer_id,
        cluster_id=cluster,
        prediction="Defect" if is_defective else "Pass",
        is_defective=is_defective,
        defect_probability=round(prob, 4),
        model_version=bundle.version,
        top_anomalies=[
            SensorAnomalyDetail(
                sensor=a.sensor,
                value=a.value,
                baseline_mean=a.baseline_mean,
                baseline_std=a.baseline_std,
                z_score=a.z_score,
                direction=a.direction,
                severity=a.severity,
            )
            for a in diagnosis.top_anomalies
        ],
    )


@router.post("/batch", response_model=BatchInferenceResponse)
async def predict_batch_file(
    file: UploadFile | None = File(None),
    filename: str | None = Query(None, description="Existing batch file in Prediction_Batch_files"),
    model_version: str | None = Query(None),
    db: Session = Depends(get_db),
):
    """Run batch inference on an uploaded CSV file or existing prediction batch."""
    from backend.app.config import PREDICTION_BATCHES_DIR

    if file:
        dest_path = PREDICTION_BATCHES_DIR / file.filename
        with open(dest_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        target_path = dest_path
        batch_name = file.filename
    elif filename:
        target_path = PREDICTION_BATCHES_DIR / filename
        batch_name = filename
    else:
        # Fall back to first available CSV in Prediction_Batch_files or generate
        csvs = list(PREDICTION_BATCHES_DIR.glob("*.csv"))
        if not csvs:
            from src.data.generator import generate_batch_files
            csvs = generate_batch_files(
                output_dir=PREDICTION_BATCHES_DIR,
                num_files=1,
                samples_per_file=120,
                num_sensors=60,
                is_training=False,
            )
        target_path = csvs[0]
        batch_name = target_path.name

    if not target_path.exists():
        raise HTTPException(status_code=404, detail=f"Target batch file {batch_name} not found.")

    output_report_path = REPORTS_DIR / f"predictions_{Path(batch_name).stem}.csv"
    try:
        summary = run_batch_inference(
            input_path=target_path,
            output_path=output_report_path,
            model_version=model_version,
            registry_dir=MODELS_DIR,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch inference failed: {e!s}")

    job_id = f"batch-{uuid.uuid4().hex[:8]}"
    record = InferenceJobModel(
        id=job_id,
        filename=batch_name,
        model_version=summary["model_version"],
        total_wafers=summary["total_wafers"],
        defects_count=summary["defects_detected"],
        yield_rate=summary["yield_rate"],
        results=summary["results"][:50],  # persist sample results
    )
    db.add(record)
    db.commit()

    return BatchInferenceResponse(
        job_id=job_id,
        model_version=summary["model_version"],
        total_wafers=summary["total_wafers"],
        defects_count=summary["defects_detected"],
        yield_rate=summary["yield_rate"],
        results=summary["results"],
    )


@router.get("/history", response_model=list[dict[str, Any]])
def get_inference_history(db: Session = Depends(get_db)):
    """Retrieve history of batch inference runs."""
    jobs = db.query(InferenceJobModel).order_by(InferenceJobModel.created_at.desc()).limit(20).all()
    return [
        {
            "id": j.id,
            "filename": j.filename,
            "model_version": j.model_version,
            "total_wafers": j.total_wafers,
            "defects_count": j.defects_count,
            "yield_rate": j.yield_rate,
            "created_at": j.created_at.isoformat(),
        }
        for j in jobs
    ]
