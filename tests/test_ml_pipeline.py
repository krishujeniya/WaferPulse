"""Unit and Integration Tests for Core MLOps Pipeline."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from pathlib import Path

from src.data.generator import generate_batch_files, generate_wafer_telemetry
from src.data.validator import TelemetryValidator
from src.features.preprocessor import TelemetryPreprocessor
from src.models.clusterer import WaferClusterer
from src.models.ensemble import ClusteredEnsembleModel
from src.models.registry import ModelRegistry
from src.monitoring.drift import assess_sensor_drift, calculate_psi
from src.explain.root_cause import diagnose_single_wafer


def test_telemetry_generator():
    """Verify synthetic wafer telemetry matches schema expectations."""
    df = generate_wafer_telemetry(num_samples=50, num_sensors=20, defect_rate=0.1, random_state=42)
    assert len(df) == 50
    assert "Wafer" in df.columns
    assert "Output" in df.columns
    assert "Sensor_1" in df.columns
    assert "Sensor_20" in df.columns
    # Check defect presence
    assert -1 in df["Output"].values
    assert 1 in df["Output"].values


def test_telemetry_validator(tmp_path):
    """Verify schema validator accepts valid batches and rejects corrupt batches."""
    validator = TelemetryValidator()

    # Valid training batch
    df_valid = generate_wafer_telemetry(num_samples=30, num_sensors=10, is_training=True)
    valid_file = tmp_path / "valid.csv"
    df_valid.to_csv(valid_file, index=False)
    rep_valid = validator.validate_file(valid_file, is_training=True)
    assert rep_valid.is_valid is True
    assert rep_valid.row_count == 30

    # Corrupt batch without Wafer column
    df_corrupt = df_valid.drop(columns=["Wafer"])
    corrupt_file = tmp_path / "corrupt.csv"
    df_corrupt.to_csv(corrupt_file, index=False)
    rep_corrupt = validator.validate_file(corrupt_file, is_training=True)
    assert rep_corrupt.is_valid is False
    assert "Wafer" in rep_corrupt.quarantine_reason


def test_preprocessor_fit_transform():
    """Verify preprocessor handles imputation, variance pruning, and scaling."""
    df = generate_wafer_telemetry(num_samples=60, num_sensors=15, missing_rate=0.05, random_state=42)
    preprocessor = TelemetryPreprocessor(null_threshold=0.35)
    X, y, wafer_ids = preprocessor.fit_transform(df)

    assert X.shape[0] == 60
    assert not np.isnan(X).any(), "Preprocessed matrix must not contain NaN"
    assert len(wafer_ids) == 60
    assert y is not None
    assert preprocessor.is_fitted is True


def test_wafer_clusterer():
    """Verify chamber K-Means clustering and optimal K assignment."""
    X = np.random.randn(80, 10)
    clusterer = WaferClusterer(min_clusters=2, max_clusters=4, random_state=42)
    labels = clusterer.fit_predict(X)

    assert len(labels) == 80
    assert clusterer.optimal_clusters in [2, 3, 4]
    assert len(clusterer.cluster_distribution) == clusterer.optimal_clusters


def test_clustered_ensemble_training_and_eval():
    """Verify model ensemble training, scoring, and metric calculation."""
    df = generate_wafer_telemetry(num_samples=100, num_sensors=15, defect_rate=0.15, random_state=42)
    preprocessor = TelemetryPreprocessor()
    X, y, _ = preprocessor.fit_transform(df)

    clusterer = WaferClusterer(min_clusters=2, max_clusters=3, random_state=42)
    cluster_labels = clusterer.fit_predict(X)

    ensemble = ClusteredEnsembleModel(random_state=42)
    ensemble.fit(X, y, cluster_labels)

    assert ensemble.is_fitted is True
    metrics = ensemble.evaluation_metrics
    assert "accuracy" in metrics
    assert "recall" in metrics
    assert "f1_score" in metrics
    assert "roc_auc" in metrics

    # Test prediction
    preds, probs = ensemble.predict(X, cluster_labels)
    assert len(preds) == 100
    assert len(probs) == 100
    assert ((probs >= 0.0) & (probs <= 1.0)).all()


def test_root_cause_diagnosis():
    """Verify top anomalous sensors attribution for defective wafers."""
    baseline_stats = {
        "Sensor_1": {"mean": 100.0, "std": 5.0},
        "Sensor_2": {"mean": 50.0, "std": 2.0},
        "Sensor_3": {"mean": 10.0, "std": 1.0},
    }
    # Sensor_2 deviates significantly (+5 std dev)
    sensor_values = {"Sensor_1": 101.0, "Sensor_2": 60.0, "Sensor_3": 10.2}

    diagnosis = diagnose_single_wafer(
        wafer_id="W-TEST-1",
        sensor_values=sensor_values,
        baseline_stats=baseline_stats,
        defect_prob=0.92,
        cluster_id=1,
        top_k=2,
    )

    assert diagnosis.is_defective is True
    assert diagnosis.top_anomalies[0].sensor == "Sensor_2"
    assert diagnosis.top_anomalies[0].severity == "CRITICAL"
    assert diagnosis.top_anomalies[0].direction == "HIGH"


def test_drift_calculation():
    """Verify PSI and KS drift assessment between distributions."""
    rng = np.random.RandomState(42)
    base = rng.normal(100, 5, 200)
    curr_stable = rng.normal(100, 5, 200)
    curr_drifted = rng.normal(130, 15, 200)

    psi_stable = calculate_psi(base, curr_stable)
    psi_drifted = calculate_psi(base, curr_drifted)

    assert psi_stable < 0.15
    assert psi_drifted > psi_stable
