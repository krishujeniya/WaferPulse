"""Background MLOps Pipeline Service."""

from __future__ import annotations

import logging
import traceback
from datetime import datetime
from pathlib import Path

import pandas as pd
from sqlalchemy.orm import Session

from backend.app.config import MODELS_DIR, TRAINING_BATCHES_DIR
from backend.app.db.database import SessionLocal
from backend.app.db.models import TrainingJobModel
from src.data.generator import generate_batch_files
from src.data.validator import TelemetryValidator
from src.features.preprocessor import TelemetryPreprocessor
from src.models.clusterer import WaferClusterer
from src.models.ensemble import ClusteredEnsembleModel
from src.models.registry import ModelRegistry

logger = logging.getLogger(__name__)


def execute_training_job_sync(job_id: str, data_dir_name: str, requested_version: str | None, set_active: bool) -> None:
    """Synchronous pipeline worker function called inside background task thread."""
    db: Session = SessionLocal()
    job = db.query(TrainingJobModel).filter(TrainingJobModel.id == job_id).first()
    if not job:
        db.close()
        return

    try:
        # Step 1: Ingestion & Validation
        job.status = "running"
        job.current_step = "Validating raw telemetry batches"
        job.progress_pct = 15
        db.commit()

        target_dir = Path(data_dir_name)
        if not target_dir.is_absolute():
            target_dir = TRAINING_BATCHES_DIR if "Training" in data_dir_name else Path(data_dir_name)

        csv_files = sorted(list(target_dir.glob("*.csv")))
        if not csv_files:
            logger.info(f"Generating synthetic training batches in {target_dir}")
            csv_files = generate_batch_files(
                output_dir=target_dir,
                num_files=4,
                samples_per_file=150,
                num_sensors=60,
                is_training=True,
                random_state_start=int(datetime.now().timestamp()) % 1000,
            )

        validator = TelemetryValidator()
        valid_dfs = []
        for f in csv_files:
            rep = validator.validate_file(f, is_training=True)
            if rep.is_valid:
                valid_dfs.append(pd.read_csv(f))

        if not valid_dfs:
            raise ValueError("All batch files failed schema validation.")

        combined_df = pd.concat(valid_dfs, ignore_index=True)
        job.total_wafers = len(combined_df)
        job.current_step = "Feature engineering & robust normalization"
        job.progress_pct = 35
        db.commit()

        # Step 2: Feature Engineering
        preprocessor = TelemetryPreprocessor(null_threshold=0.35, impute_strategy="median")
        X, y, wafer_ids = preprocessor.fit_transform(combined_df)
        job.features_retained = len(preprocessor.feature_columns)

        # Step 3: Chamber Clustering
        job.current_step = "K-Means chamber regime clustering"
        job.progress_pct = 60
        db.commit()

        clusterer = WaferClusterer(min_clusters=2, max_clusters=4, random_state=42)
        cluster_labels = clusterer.fit_predict(X)
        job.clusters_count = clusterer.optimal_clusters

        # Step 4: Training Ensembles
        job.current_step = "Training cluster-specific ensemble classifiers"
        job.progress_pct = 80
        db.commit()

        ensemble = ClusteredEnsembleModel(random_state=42)
        ensemble.fit(X, y, cluster_labels)
        metrics = ensemble.evaluation_metrics

        # Step 5: Packaging & Registration
        job.current_step = "Packaging artifacts and model registration"
        job.progress_pct = 95
        db.commit()

        version = requested_version or f"v{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        registry = ModelRegistry(registry_dir=MODELS_DIR)
        registry.register_model(
            version=version,
            preprocessor=preprocessor,
            clusterer=clusterer,
            ensemble=ensemble,
            metrics=metrics,
            dataset_name=target_dir.name,
            set_active=set_active,
        )

        job.status = "completed"
        job.current_step = "Model registered and verified"
        job.progress_pct = 100
        job.model_version = version
        job.metrics = metrics
        job.completed_at = datetime.utcnow()
        db.commit()
        logger.info(f"Training job {job_id} successfully completed for version {version}")

    except Exception as e:
        logger.error(f"Training job {job_id} failed: {e}", exc_info=True)
        job.status = "failed"
        job.current_step = "Pipeline execution failed"
        job.error_message = f"{e!s}\n{traceback.format_exc()}"
        db.commit()
    finally:
        db.close()
