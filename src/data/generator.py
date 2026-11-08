"""Industrial Wafer Telemetry Data Generator.

Generates realistic semiconductor sensor data mimicking photolithography,
chemical mechanical planarization (CMP), and plasma etching processes.
Includes multi-chamber operating regimes and realistic sensor fault injection.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd


def generate_wafer_telemetry(
    num_samples: int = 400,
    num_sensors: int = 60,
    defect_rate: float = 0.08,
    missing_rate: float = 0.02,
    random_state: int = 42,
    is_training: bool = True,
) -> pd.DataFrame:
    """Generate synthetic but physically grounded semiconductor sensor data.

    Args:
        num_samples: Number of wafer runs to simulate.
        num_sensors: Number of sensor telemetry columns (Sensor_1 to Sensor_N).
        defect_rate: Target fraction of defective wafers (Output = -1).
        missing_rate: Fraction of sensor readings that are sporadically missing (NaN).
        random_state: Seed for reproducibility.
        is_training: If True, includes 'Output' column (1 = Good, -1 = Defect).

    Returns:
        pd.DataFrame containing 'Wafer' ID and sensor telemetry (and 'Output' if training).
    """
    rng = np.random.RandomState(random_state)

    # 3 distinct fabrication chamber regimes (K-Means clusters)
    # Different baseline pressure, temperature, RF power, gas flows
    chambers = ["Chamber_A", "Chamber_B", "Chamber_C"]
    chamber_assignments = rng.choice(chambers, size=num_samples, p=[0.45, 0.35, 0.20])

    sensor_columns = [f"Sensor_{i+1}" for i in range(num_sensors)]
    data_matrix = np.zeros((num_samples, num_sensors))

    # Baseline sensor means and variances across chambers
    base_means = rng.uniform(10.0, 500.0, size=num_sensors)
    base_stds = rng.uniform(0.5, 12.0, size=num_sensors)

    # Chamber offsets to create natural clusters
    chamber_offsets: dict[str, np.ndarray] = {
        "Chamber_A": np.zeros(num_sensors),
        "Chamber_B": rng.normal(0, base_stds * 1.5, size=num_sensors),
        "Chamber_C": rng.normal(0, base_stds * 2.2, size=num_sensors),
    }

    # Add 2 zero-variance sensors to simulate dead sensors that the pipeline must prune
    dead_sensors = [5, 18]

    # Generate normal telemetry
    for i in range(num_samples):
        ch = chamber_assignments[i]
        sample_mean = base_means + chamber_offsets[ch]
        data_matrix[i, :] = rng.normal(sample_mean, base_stds)

    # Force dead sensors to have zero variance
    for s_idx in dead_sensors:
        if s_idx < num_sensors:
            data_matrix[:, s_idx] = base_means[s_idx]

    # Inject defects and anomalies
    labels = np.ones(num_samples, dtype=int)  # 1 = Normal/Good
    num_defects = int(num_samples * defect_rate)
    defect_indices = rng.choice(num_samples, size=num_defects, replace=False)
    labels[defect_indices] = -1  # -1 = Defective / Faulty

    # In defective wafers, inject systematic sensor drifts in critical sensor channels
    # E.g., Sensor_10 (RF bias), Sensor_25 (Chamber pressure), Sensor_42 (Coolant flow)
    fault_sensors = [10, 24, 41]
    for idx in defect_indices:
        for fs in fault_sensors:
            if fs < num_sensors:
                shift_direction = rng.choice([-1, 1])
                # 4 to 8 standard deviations out of spec
                data_matrix[idx, fs] += shift_direction * rng.uniform(4.0, 8.0) * base_stds[fs]

    # Inject sporadic missing sensor values (sensor timeouts / dropped telemetry packets)
    if missing_rate > 0:
        mask = rng.rand(*data_matrix.shape) < missing_rate
        # Keep dead sensors intact for deterministic pruning check
        for ds in dead_sensors:
            if ds < num_sensors:
                mask[:, ds] = False
        data_matrix[mask] = np.nan

    # Build DataFrame
    df = pd.DataFrame(data_matrix, columns=sensor_columns)

    # Generate realistic Wafer IDs: e.g. Wafer_20261108_143000_001
    now_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    wafer_ids = [f"Wafer_{now_str}_{i+1:04d}" for i in range(num_samples)]
    df.insert(0, "Wafer", wafer_ids)

    if is_training:
        df["Output"] = labels

    return df


def generate_batch_files(
    output_dir: str | Path,
    num_files: int = 5,
    samples_per_file: int = 100,
    num_sensors: int = 60,
    is_training: bool = True,
    random_state_start: int = 100,
) -> list[Path]:
    """Generate a sequence of batch CSV files on disk.

    Args:
        output_dir: Destination directory.
        num_files: Number of batch CSV files to create.
        samples_per_file: Rows per file.
        num_sensors: Number of sensor columns.
        is_training: Whether to include Output label column.
        random_state_start: Seed offset.

    Returns:
        List of generated file Paths.
    """
    path = Path(output_dir)
    path.mkdir(parents=True, exist_ok=True)
    generated: list[Path] = []

    for i in range(num_files):
        df = generate_wafer_telemetry(
            num_samples=samples_per_file,
            num_sensors=num_sensors,
            defect_rate=0.07,
            missing_rate=0.015,
            random_state=random_state_start + i,
            is_training=is_training,
        )
        timestamp = datetime.now().strftime("%d%m%Y_%H%M%S")
        filename = f"Wafer_{timestamp}_{i+1:02d}.csv"
        file_path = path / filename
        df.to_csv(file_path, index=False)
        generated.append(file_path)

    return generated
