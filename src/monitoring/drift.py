"""Sensor Drift and Fab Telemetry Monitoring Engine.

Calculates Population Stability Index (PSI) and two-sample Kolmogorov-Smirnov
tests to detect sensor degradation, chamber drift, and tool wear.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import numpy as np
import pandas as pd
from scipy.stats import ks_2samp


@dataclass
class SensorDriftReport:
    """Drift metrics for a single sensor channel."""

    sensor: str
    psi: float
    ks_statistic: float
    ks_p_value: float
    status: str  # "STABLE", "MODERATE_DRIFT", "CRITICAL_DRIFT"
    baseline_mean: float
    current_mean: float
    mean_shift_percent: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class BatchDriftSummary:
    """System-level drift audit across all monitored sensors."""

    total_sensors_monitored: int
    stable_count: int
    moderate_drift_count: int
    critical_drift_count: int
    overall_status: str  # "HEALTHY", "WARNING", "CRITICAL"
    top_drifted_sensors: list[SensorDriftReport]

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["top_drifted_sensors"] = [s.to_dict() for s in self.top_drifted_sensors]
        return d


def calculate_psi(
    expected: np.ndarray,
    actual: np.ndarray,
    num_buckets: int = 10,
    epsilon: float = 1e-4,
) -> float:
    """Calculate Population Stability Index between baseline and current distributions."""
    expected = expected[~np.isnan(expected)]
    actual = actual[~np.isnan(actual)]

    if len(expected) < 10 or len(actual) < 10:
        return 0.0

    # Determine quantile bin edges from expected/baseline
    quantiles = np.linspace(0, 100, num_buckets + 1)
    try:
        bin_edges = np.percentile(expected, quantiles)
    except Exception:
        return 0.0

    # Ensure monotonic strictly increasing bin edges
    bin_edges = np.unique(bin_edges)
    if len(bin_edges) < 2:
        return 0.0

    bin_edges[0] = -np.inf
    bin_edges[-1] = np.inf

    expected_counts, _ = np.histogram(expected, bins=bin_edges)
    actual_counts, _ = np.histogram(actual, bins=bin_edges)

    expected_pct = expected_counts / len(expected)
    actual_pct = actual_counts / len(actual)

    # Avoid zero division with epsilon smoothing
    expected_pct = np.clip(expected_pct, epsilon, 1.0)
    actual_pct = np.clip(actual_pct, epsilon, 1.0)

    psi_val = np.sum((actual_pct - expected_pct) * np.log(actual_pct / expected_pct))
    return float(max(0.0, psi_val))


def assess_sensor_drift(
    baseline_df: pd.DataFrame,
    current_df: pd.DataFrame,
    sensor_columns: list[str] | None = None,
    psi_critical_threshold: float = 0.25,
    psi_warning_threshold: float = 0.10,
) -> BatchDriftSummary:
    """Assess drift across all sensor channels between baseline and production batches."""
    if sensor_columns is None:
        sensor_columns = [
            c for c in baseline_df.columns if c in current_df.columns and c.startswith("Sensor_")
        ]

    sensor_reports: list[SensorDriftReport] = []
    stable_cnt = 0
    mod_cnt = 0
    crit_cnt = 0

    for sensor in sensor_columns:
        base_vals = baseline_df[sensor].dropna().to_numpy()
        curr_vals = current_df[sensor].dropna().to_numpy()

        if len(base_vals) < 5 or len(curr_vals) < 5:
            continue

        # PSI
        psi = calculate_psi(base_vals, curr_vals)

        # KS test
        try:
            ks_res = ks_2samp(base_vals, curr_vals)
            ks_stat = float(ks_res.statistic)
            ks_p = float(ks_res.pvalue)
        except Exception:
            ks_stat = 0.0
            ks_p = 1.0

        # Means and relative shift
        b_mean = float(np.mean(base_vals))
        c_mean = float(np.mean(curr_vals))
        mean_shift_pct = (
            abs(c_mean - b_mean) / (abs(b_mean) + 1e-6) * 100.0
        )

        if psi >= psi_critical_threshold:
            status = "CRITICAL_DRIFT"
            crit_cnt += 1
        elif psi >= psi_warning_threshold:
            status = "MODERATE_DRIFT"
            mod_cnt += 1
        else:
            status = "STABLE"
            stable_cnt += 1

        sensor_reports.append(
            SensorDriftReport(
                sensor=sensor,
                psi=round(psi, 4),
                ks_statistic=round(ks_stat, 4),
                ks_p_value=round(ks_p, 4),
                status=status,
                baseline_mean=round(b_mean, 4),
                current_mean=round(c_mean, 4),
                mean_shift_percent=round(mean_shift_pct, 2),
            )
        )

    # Sort descending by PSI
    sensor_reports.sort(key=lambda x: x.psi, reverse=True)

    if crit_cnt > 0:
        overall_status = "CRITICAL"
    elif mod_cnt > 0:
        overall_status = "WARNING"
    else:
        overall_status = "HEALTHY"

    return BatchDriftSummary(
        total_sensors_monitored=len(sensor_reports),
        stable_count=stable_cnt,
        moderate_drift_count=mod_cnt,
        critical_drift_count=crit_cnt,
        overall_status=overall_status,
        top_drifted_sensors=sensor_reports[:10],
    )
