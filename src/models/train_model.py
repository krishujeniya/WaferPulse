"""Train Model Pipeline Runner.

Ingests training batch files, validates data contracts, executes preprocessing,
fits chamber regime clustering, trains clustered ensembles, and registers
the production model bundle.
"""

from __future__ import annotations

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

from src.data.generator import generate_batch_files
from src.data.validator import TelemetryValidator
from src.features.preprocessor import TelemetryPreprocessor
from src.models.clusterer import WaferClusterer
from src.models.ensemble import ClusteredEnsembleModel
from src.models.registry import ModelRegistry

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("train_model")


def run_training_pipeline(
    data_dir: str | Path = "data/raw",
    model_version: str | None = None,
    registry_dir: str | Path = "models",
    auto_generate_if_empty: bool = True,
    set_active: bool = True,
) -> dict:
    """Execute end-to-end training pipeline.

    Returns:
        Dictionary containing run summary and metrics.
    """
    data_path = Path(data_dir)
    data_path.mkdir(parents=True, exist_ok=True)

    # 1. Check for CSV files; check data_dir and fallback to Training_Batch_Files
    csv_files = sorted(list(data_path.glob("*.csv")))
    if not csv_files:
        alt_path = Path("Training_Batch_Files")
        if alt_path.is_dir():
            csv_files = sorted(list(alt_path.glob("*.csv")))
    if not csv_files and auto_generate_if_empty:
        logger.info(f"No CSVs found in {data_path}; generating synthetic baseline telemetry batches...")
        csv_files = generate_batch_files(
            output_dir=data_path,
            num_files=4,
            samples_per_file=150,
            num_sensors=60,
            is_training=True,
            random_state_start=42,
        )

    if not csv_files:
        raise FileNotFoundError(f"No valid CSV batches found in {data_path}")

    # 2. Ingest and Validate batches
    validator = TelemetryValidator()
    valid_dfs: list[pd.DataFrame] = []
    quarantine_dir = data_path / "quarantine"

    for f in csv_files:
        report = validator.validate_file(f, is_training=True, quarantine_dir=quarantine_dir)
        if report.is_valid:
            df = pd.read_csv(f)
            valid_dfs.append(df)
            logger.info(f"Validated {f.name}: {report.row_count} rows, {report.column_count} cols")
        else:
            logger.warning(f"Batch rejected: {f.name} - {report.quarantine_reason}")

    if not valid_dfs:
        raise ValueError("No batch files passed schema validation.")

    combined_df = pd.concat(valid_dfs, ignore_index=True)
    logger.info(f"Combined dataset: {len(combined_df)} wafers across {len(combined_df.columns)} columns")

    # 3. Feature Engineering & Preprocessing
    logger.info("Fitting telemetry preprocessor...")
    preprocessor = TelemetryPreprocessor(null_threshold=0.35, impute_strategy="median")
    X, y, wafer_ids = preprocessor.fit_transform(combined_df)

    if y is None:
        raise ValueError("Target 'Output' was not found in validated training data.")

    logger.info(
        f"Preprocessing complete. Kept {len(preprocessor.feature_columns)} features. "
        f"Pruned high-null: {len(preprocessor.dropped_high_null_cols)}, "
        f"Pruned zero-var: {len(preprocessor.dropped_zero_var_cols)}"
    )

    # 4. Chamber Operational Regime Clustering
    logger.info("Fitting chamber K-Means clustering...")
    clusterer = WaferClusterer(min_clusters=2, max_clusters=4, random_state=42)
    cluster_labels = clusterer.fit_predict(X)
    logger.info(
        f"Identified {clusterer.optimal_clusters} operational clusters. "
        f"Distribution: {clusterer.cluster_distribution}"
    )

    # 5. Clustered Ensemble Modeling
    logger.info("Training cluster-specific ensemble classifiers...")
    ensemble = ClusteredEnsembleModel(random_state=42)
    ensemble.fit(X, y, cluster_labels)
    metrics = ensemble.evaluation_metrics
    logger.info(f"Evaluation metrics: {metrics}")

    # 6. Model Registration
    version = model_version or f"v{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    registry = ModelRegistry(registry_dir=registry_dir)
    registry.register_model(
        version=version,
        preprocessor=preprocessor,
        clusterer=clusterer,
        ensemble=ensemble,
        metrics=metrics,
        dataset_name=data_path.name,
        set_active=set_active,
    )
    logger.info(f"Successfully registered and activated model version: {version}")

    return {
        "status": "success",
        "version": version,
        "metrics": metrics,
        "cluster_distribution": clusterer.cluster_distribution,
        "features_retained": len(preprocessor.feature_columns),
        "total_wafers_trained": len(combined_df),
    }


def main():
    parser = argparse.ArgumentParser(description="WaferGuard MLOps Training Pipeline")
    parser.add_argument("--data-dir", default="data/raw", help="Path to raw training batches")
    parser.add_argument("--version", default=None, help="Optional explicit model version name")
    parser.add_argument("--registry-dir", default="models", help="Model registry directory")
    args = parser.parse_args()

    try:
        run_training_pipeline(
            data_dir=args.data_dir,
            model_version=args.version,
            registry_dir=args.registry_dir,
        )
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
