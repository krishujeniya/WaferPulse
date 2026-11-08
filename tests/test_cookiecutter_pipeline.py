"""Tests for Cookiecutter Data Science pipeline stages."""

from __future__ import annotations

from pathlib import Path
import pytest

from src.data.generator import generate_batch_files
from src.data.make_dataset import make_dataset
from src.features.build_features import build_features
from src.visualization.visualize import generate_drift_figure, generate_wafer_map_figure


def test_cookiecutter_make_dataset_and_features_pipeline(tmp_path):
    """Verify end-to-end flow from data/raw to data/interim to data/processed."""
    raw_dir = tmp_path / "raw"
    interim_file = tmp_path / "interim" / "clean_telemetry.csv"
    processed_file = tmp_path / "processed" / "features.csv"
    preprocessor_artifact = tmp_path / "models" / "preprocessor.joblib"

    # 1. Ingest raw batches into interim
    df_interim = make_dataset(
        input_filepath=raw_dir,
        output_filepath=interim_file,
        auto_generate_if_missing=True,
    )
    assert interim_file.is_file()
    assert len(df_interim) > 0
    assert "Wafer" in df_interim.columns
    assert "Output" in df_interim.columns

    # 2. Build features into processed
    df_processed = build_features(
        input_filepath=interim_file,
        output_filepath=processed_file,
        preprocessor_artifact_path=preprocessor_artifact,
    )
    assert processed_file.is_file()
    assert preprocessor_artifact.is_file()
    assert len(df_processed) == len(df_interim)


def test_cookiecutter_visualize_figures(tmp_path):
    """Verify figure generation for reports/figures."""
    wafer_fig = tmp_path / "wafer_die_map.svg"
    drift_fig = tmp_path / "sensor_drift.svg"

    res_wafer = generate_wafer_map_figure(wafer_fig)
    res_drift = generate_drift_figure(drift_fig)

    assert res_wafer.is_file()
    assert res_drift.is_file()
    assert res_wafer.stat().st_size > 500
    assert res_drift.stat().st_size > 500
