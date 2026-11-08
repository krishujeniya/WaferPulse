"""API Integration Tests for WaferPulse FastAPI Endpoints."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from backend.app.db.database import init_db
from backend.app.main import app

# Ensure tables are initialized before tests run
init_db()
client = TestClient(app)


def test_health_endpoint():
    """Verify system health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "WaferPulse" in data["service"]


def test_datasets_endpoints():
    """Verify dataset listing, sample generation, and preview."""
    # Generate sample batches
    gen_res = client.post("/api/v1/datasets/generate-sample?file_type=training&batch_count=1&samples_per_batch=40")
    assert gen_res.status_code == 200
    batches = gen_res.json()
    assert len(batches) == 1
    sample_file = batches[0]["filename"]

    # List datasets
    list_res = client.get("/api/v1/datasets")
    assert list_res.status_code == 200
    datasets = list_res.json()
    assert any(d["filename"] == sample_file for d in datasets)

    # Preview dataset
    prev_res = client.get(f"/api/v1/datasets/{sample_file}/preview")
    assert prev_res.status_code == 200
    preview = prev_res.json()
    assert preview["filename"] == sample_file
    assert len(preview["preview_rows"]) > 0


def test_models_registry_endpoints():
    """Verify model listing and active model endpoints."""
    res = client.get("/api/v1/models")
    assert res.status_code == 200
    models = res.json()
    assert isinstance(models, list)
    assert len(models) > 0  # we trained a model earlier

    active_res = client.get("/api/v1/models/active")
    assert active_res.status_code == 200
    active_m = active_res.json()
    assert "version" in active_m
    assert "metrics" in active_m


def test_single_prediction_endpoint():
    """Verify single wafer prediction and root cause response."""
    # Fetch active model to get feature names
    active_m = client.get("/api/v1/models/active").json()
    features = active_m["feature_columns"]

    sensor_payload = {f: 100.0 for f in features}
    payload = {
        "wafer_id": "TEST_WAFER_001",
        "sensors": sensor_payload,
    }

    res = client.post("/api/v1/predict/single", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["wafer_id"] == "TEST_WAFER_001"
    assert data["prediction"] in ["Pass", "Defect"]
    assert "cluster_id" in data
    assert "top_anomalies" in data


def test_monitoring_drift_endpoint():
    """Verify drift assessment API."""
    res = client.get("/api/v1/monitoring/drift")
    assert res.status_code == 200
    data = res.json()
    assert "total_sensors_monitored" in data
    assert "overall_status" in data
    assert isinstance(data["top_drifted_sensors"], list)


def test_fab_overview_endpoint():
    """Verify fab overview and chamber health metrics."""
    res = client.get("/api/v1/monitoring/fab-overview")
    assert res.status_code == 200
    data = res.json()
    assert data["system_status"] == "ONLINE"
    assert len(data["chambers"]) == 3
