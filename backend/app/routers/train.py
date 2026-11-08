"""Training Pipeline Orchestration Endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.db.database import get_db
from backend.app.db.models import TrainingJobModel
from backend.app.schemas.training import TrainingJobStatus, TrainTriggerRequest
from backend.app.services.pipeline_service import execute_training_job_sync

router = APIRouter(prefix="/train", tags=["Training"])


@router.post("", response_model=TrainingJobStatus)
def trigger_training_pipeline(
    payload: TrainTriggerRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Trigger an asynchronous MLOps training run."""
    job_id = f"job-{uuid.uuid4().hex[:8]}"

    job = TrainingJobModel(
        id=job_id,
        status="queued",
        current_step="Queued for execution",
        progress_pct=0,
        dataset_name=payload.data_dir,
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    # Dispatch to background task worker
    background_tasks.add_task(
        execute_training_job_sync,
        job_id=job_id,
        data_dir_name=payload.data_dir or "Training_Batch_Files",
        requested_version=payload.version,
        set_active=payload.set_active,
    )

    return job


@router.get("/jobs", response_model=list[TrainingJobStatus])
def list_training_jobs(db: Session = Depends(get_db)):
    """List recent training jobs ordered by creation timestamp."""
    return db.query(TrainingJobModel).order_by(TrainingJobModel.created_at.desc()).all()


@router.get("/jobs/{job_id}", response_model=TrainingJobStatus)
def get_job_status(job_id: str, db: Session = Depends(get_db)):
    """Get real-time execution status and evaluation metrics for a job."""
    job = db.query(TrainingJobModel).filter(TrainingJobModel.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Training job not found")
    return job
