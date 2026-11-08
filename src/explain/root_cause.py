"""Sensor Root-Cause Anomaly Attribution Engine.

Analyzes defective wafers to isolate root-cause sensor anomalies:
- Calculates per-sensor Z-score deviations against baseline cluster statistics
- Ranks top-K contributing sensors causing the wafer fault
- Flags operational severity (Nominal, Warning, Critical) and directional bias
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import pandas as pd


@dataclass
class SensorAnomaly:
    """Anomalous sensor deviation detail for root-cause diagnosis."""

    sensor: str
    value: float
    baseline_mean: float
    baseline_std: float
    z_score: float
    direction: str  # "HIGH" or "LOW"
    severity: str  # "CRITICAL", "WARNING", "NOMINAL"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class WaferDiagnosis:
    """Diagnostic report for a single wafer run."""

    wafer_id: str
    is_defective: bool
    defect_probability: float
    cluster_id: int
    top_anomalies: list[SensorAnomaly]

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["top_anomalies"] = [a.to_dict() for a in self.top_anomalies]
        return d


def diagnose_single_wafer(
    wafer_id: str,
    sensor_values: dict[str, float],
    baseline_stats: dict[str, dict[str, float]],
    defect_prob: float,
    cluster_id: int,
    top_k: int = 5,
) -> WaferDiagnosis:
    """Isolate top anomalous sensors contributing to a wafer deviation.

    Args:
        wafer_id: Unique wafer tracking code.
        sensor_values: Key-value map of sensor readings.
        baseline_stats: Mean and std per sensor from preprocessor.
        defect_prob: Model-predicted defect probability.
        cluster_id: Chamber regime cluster ID.
        top_k: Number of highest deviating sensors to return.

    Returns:
        WaferDiagnosis containing top anomalous sensors.
    """
    anomalies: list[SensorAnomaly] = []

    for sensor_name, stats in baseline_stats.items():
        if sensor_name not in sensor_values or pd.isna(sensor_values[sensor_name]):
            continue

        val = float(sensor_values[sensor_name])
        mean = stats.get("mean", 0.0)
        std = stats.get("std", 1.0)
        std = std if std > 1e-6 else 1.0

        z = (val - mean) / std
        abs_z = abs(z)

        if abs_z >= 3.0:
            severity = "CRITICAL"
        elif abs_z >= 2.0:
            severity = "WARNING"
        else:
            severity = "NOMINAL"

        direction = "HIGH" if z > 0 else "LOW"

        anomalies.append(
            SensorAnomaly(
                sensor=sensor_name,
                value=round(val, 4),
                baseline_mean=round(mean, 4),
                baseline_std=round(std, 4),
                z_score=round(z, 2),
                direction=direction,
                severity=severity,
            )
        )

    # Sort descending by absolute Z-score deviation
    anomalies.sort(key=lambda a: abs(a.z_score), reverse=True)
    top_anomalies = anomalies[:top_k]

    return WaferDiagnosis(
        wafer_id=wafer_id,
        is_defective=defect_prob >= 0.5,
        defect_probability=round(defect_prob, 4),
        cluster_id=int(cluster_id),
        top_anomalies=top_anomalies,
    )
