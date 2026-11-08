"""Chamber & Operational Regime Clustering Module.

Groups wafers into operational clusters using K-Means with Silhouette Optimization.
Reflects physical semiconductor chamber variations (e.g., CMP planarizer wear,
RF plasma chamber baseline differences).
"""

from __future__ import annotations

from pathlib import Path

import joblib
import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score


class WaferClusterer:
    """Clusters wafer telemetry into operational regime clusters."""

    def __init__(
        self,
        min_clusters: int = 2,
        max_clusters: int = 4,
        random_state: int = 42,
    ):
        self.min_clusters = min_clusters
        self.max_clusters = max_clusters
        self.random_state = random_state
        self.kmeans: KMeans | None = None
        self.optimal_clusters: int = 2
        self.silhouette_scores: dict[int, float] = {}
        self.cluster_distribution: dict[int, int] = {}
        self.is_fitted: bool = False

    def fit(self, X: np.ndarray) -> WaferClusterer:
        """Find optimal cluster count and fit KMeans estimator.

        Args:
            X: Standardized feature matrix (samples, features).

        Returns:
            Fitted instance.
        """
        n_samples = X.shape[0]
        max_k = min(self.max_clusters, max(2, n_samples // 15))
        min_k = min(self.min_clusters, max_k)

        best_score = -1.0
        best_k = min_k
        self.silhouette_scores = {}

        if n_samples < 20 or min_k == max_k:
            best_k = min_k
        else:
            for k in range(min_k, max_k + 1):
                try:
                    km = KMeans(n_clusters=k, random_state=self.random_state, n_init=10)
                    labels = km.fit_predict(X)
                    # Check that we have at least 2 distinct labels
                    if len(np.unique(labels)) > 1:
                        score = float(silhouette_score(X, labels, sample_size=min(500, n_samples)))
                        self.silhouette_scores[k] = score
                        if score > best_score:
                            best_score = score
                            best_k = k
                except Exception:
                    continue

        self.optimal_clusters = best_k
        self.kmeans = KMeans(
            n_clusters=self.optimal_clusters,
            random_state=self.random_state,
            n_init=10,
        )
        labels = self.kmeans.fit_predict(X)
        self.cluster_distribution = {
            int(c): int(count) for c, count in zip(*np.unique(labels, return_counts=True))
        }
        self.is_fitted = True
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Assign cluster IDs to new telemetry samples."""
        if not self.is_fitted or self.kmeans is None:
            raise RuntimeError("WaferClusterer must be fitted before predict.")
        return self.kmeans.predict(X)

    def fit_predict(self, X: np.ndarray) -> np.ndarray:
        """Fit and assign cluster IDs."""
        return self.fit(X).predict(X)

    def save(self, file_path: str | Path) -> None:
        """Serialize clusterer to disk."""
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self, path)

    @classmethod
    def load(cls, file_path: str | Path) -> WaferClusterer:
        """Deserialize clusterer from disk."""
        path = Path(file_path)
        if not path.is_file():
            raise FileNotFoundError(f"Clusterer artifact not found at {path}")
        return joblib.load(path)
