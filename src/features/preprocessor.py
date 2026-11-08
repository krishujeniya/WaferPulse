"""Feature Engineering and Telemetry Preprocessing Pipeline.

Handles:
- Missing value imputation using median/KNN strategies
- Zero-variance and dead sensor column removal
- Collinear or null-dominated sensor pruning
- Robust scaling for anomaly-resistant telemetry
- Artifact serialization for training/serving parity
"""

from __future__ import annotations

from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import RobustScaler


class TelemetryPreprocessor:
    """Preprocesses wafer sensor data and maintains state across train and inference."""

    def __init__(
        self,
        null_threshold: float = 0.35,
        impute_strategy: str = "median",
    ):
        self.null_threshold = null_threshold
        self.impute_strategy = impute_strategy
        self.imputer: SimpleImputer | None = None
        self.scaler: RobustScaler | None = None
        self.dropped_high_null_cols: list[str] = []
        self.dropped_zero_var_cols: list[str] = []
        self.feature_columns: list[str] = []
        self.baseline_stats: dict[str, dict[str, float]] = {}
        self.is_fitted: bool = False

    def fit(self, df: pd.DataFrame) -> TelemetryPreprocessor:
        """Fit preprocessor parameters on raw training DataFrame."""
        # Exclude non-telemetry columns
        excluded = {"Wafer", "Output"}
        candidate_cols = [c for c in df.columns if c not in excluded]

        # 1. Detect high-null columns
        null_ratios = df[candidate_cols].isna().mean()
        self.dropped_high_null_cols = [
            str(col) for col, r in null_ratios.items() if r > self.null_threshold
        ]
        remaining = [c for c in candidate_cols if c not in self.dropped_high_null_cols]

        # 2. Detect zero-variance (constant) sensor columns
        stds = df[remaining].std(skipna=True)
        self.dropped_zero_var_cols = [
            str(col) for col, s in stds.items() if np.isnan(s) or s == 0.0
        ]
        self.feature_columns = [
            c for c in remaining if c not in self.dropped_zero_var_cols
        ]

        if not self.feature_columns:
            raise ValueError("All candidate sensor columns were pruned during preprocessing fit.")

        # 3. Fit Imputer
        self.imputer = SimpleImputer(strategy=self.impute_strategy)
        imputed_data = self.imputer.fit_transform(df[self.feature_columns])

        # 4. Fit Scaler
        self.scaler = RobustScaler()
        self.scaler.fit(imputed_data)

        # 5. Store baseline statistics for root cause analysis & drift
        self.baseline_stats = {}
        for idx, col in enumerate(self.feature_columns):
            col_vals = imputed_data[:, idx]
            self.baseline_stats[col] = {
                "mean": float(np.mean(col_vals)),
                "std": float(np.std(col_vals)) if np.std(col_vals) > 0 else 1.0,
                "median": float(np.median(col_vals)),
                "q25": float(np.percentile(col_vals, 25)),
                "q75": float(np.percentile(col_vals, 75)),
            }

        self.is_fitted = True
        return self

    def transform(self, df: pd.DataFrame) -> tuple[np.ndarray, np.ndarray | None, list[str]]:
        """Transform DataFrame using fitted transformers.

        Returns:
            Tuple of (scaled_feature_matrix, targets_if_present, wafer_ids)
        """
        if not self.is_fitted or self.imputer is None or self.scaler is None:
            raise RuntimeError("TelemetryPreprocessor must be fitted before calling transform.")

        wafer_ids = df["Wafer"].astype(str).tolist() if "Wafer" in df.columns else [f"Wafer_{i}" for i in range(len(df))]
        
        # Check and handle features
        missing_features = [c for c in self.feature_columns if c not in df.columns]
        if missing_features:
            raise ValueError(f"Input data is missing {len(missing_features)} expected features: {missing_features[:5]}")

        feature_df = df[self.feature_columns]
        imputed = self.imputer.transform(feature_df)
        scaled = self.scaler.transform(imputed)

        targets = None
        if "Output" in df.columns:
            targets = df["Output"].to_numpy()

        return scaled, targets, wafer_ids

    def fit_transform(self, df: pd.DataFrame) -> tuple[np.ndarray, np.ndarray | None, list[str]]:
        """Fit and transform in a single call."""
        return self.fit(df).transform(df)

    def save(self, file_path: str | Path) -> None:
        """Serialize preprocessor bundle to disk."""
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self, path)

    @classmethod
    def load(cls, file_path: str | Path) -> TelemetryPreprocessor:
        """Deserialize preprocessor bundle from disk."""
        path = Path(file_path)
        if not path.is_file():
            raise FileNotFoundError(f"Preprocessor artifact not found at {path}")
        return joblib.load(path)
