"""Model Registry and Artifact Versioning Engine.

Manages versioned model artifacts, staging/production state machines,
audit logs, and zero-downtime model promotion/rollback.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from src.features.preprocessor import TelemetryPreprocessor
from src.models.clusterer import WaferClusterer
from src.models.ensemble import ClusteredEnsembleModel

logger = logging.getLogger(__name__)


@dataclass
class ModelBundle:
    """Loaded production-ready model artifact bundle."""

    version: str
    preprocessor: TelemetryPreprocessor
    clusterer: WaferClusterer
    ensemble: ClusteredEnsembleModel
    metadata: dict[str, Any]


class ModelRegistry:
    """Local file-based artifact registry for reproducible model management."""

    def __init__(self, registry_dir: str | Path = "artifacts/models"):
        self.registry_dir = Path(registry_dir)
        self.registry_dir.mkdir(parents=True, exist_ok=True)
        self.pointer_file = self.registry_dir / "active_model.json"

    def register_model(
        self,
        version: str,
        preprocessor: TelemetryPreprocessor,
        clusterer: WaferClusterer,
        ensemble: ClusteredEnsembleModel,
        metrics: dict[str, Any],
        dataset_name: str = "batch_training",
        set_active: bool = False,
    ) -> Path:
        """Package and register a new versioned model artifact."""
        model_dir = self.registry_dir / version
        model_dir.mkdir(parents=True, exist_ok=True)

        # Save constituent artifacts
        preprocessor.save(model_dir / "preprocessor.joblib")
        clusterer.save(model_dir / "clusterer.joblib")
        ensemble.save(model_dir / "ensemble.joblib")

        # Save metadata
        metadata = {
            "version": version,
            "created_at": datetime.now().isoformat(),
            "status": "production" if set_active else "staging",
            "metrics": metrics,
            "dataset_name": dataset_name,
            "features_count": len(preprocessor.feature_columns),
            "feature_columns": preprocessor.feature_columns,
            "clusters_count": clusterer.optimal_clusters,
            "dropped_high_null": preprocessor.dropped_high_null_cols,
            "dropped_zero_var": preprocessor.dropped_zero_var_cols,
        }

        with open(model_dir / "metadata.json", "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)

        if set_active or not self.pointer_file.exists():
            self.set_active_version(version)

        logger.info(f"Registered model artifact: {version} (active={set_active})")
        return model_dir

    def set_active_version(self, version: str) -> None:
        """Promote a specific model version to production."""
        target_dir = self.registry_dir / version
        if not target_dir.is_dir():
            raise FileNotFoundError(f"Cannot promote nonexistent model version {version}")

        # Record previous version for rollback
        previous_version = None
        if self.pointer_file.exists():
            try:
                with open(self.pointer_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    previous_version = data.get("active_version")
            except Exception:
                pass

        pointer_data = {
            "active_version": version,
            "promoted_at": datetime.now().isoformat(),
            "previous_version": previous_version,
        }

        with open(self.pointer_file, "w", encoding="utf-8") as f:
            json.dump(pointer_data, f, indent=2)

        # Update metadata status
        meta_file = target_dir / "metadata.json"
        if meta_file.exists():
            with open(meta_file, "r+", encoding="utf-8") as f:
                data = json.load(f)
                data["status"] = "production"
                f.seek(0)
                json.dump(data, f, indent=2)
                f.truncate()

    def get_active_version(self) -> str | None:
        """Return the version string of the currently active model."""
        if not self.pointer_file.exists():
            # Return latest if any exist
            models = self.list_models()
            return models[0]["version"] if models else None
        try:
            with open(self.pointer_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("active_version")
        except Exception:
            return None

    def load_bundle(self, version: str | None = None) -> ModelBundle:
        """Load the active or specified model bundle into memory."""
        v = version or self.get_active_version()
        if not v:
            raise FileNotFoundError("No models registered in the registry.")

        target_dir = self.registry_dir / v
        if not target_dir.is_dir():
            raise FileNotFoundError(f"Model directory {target_dir} does not exist.")

        preprocessor = TelemetryPreprocessor.load(target_dir / "preprocessor.joblib")
        clusterer = WaferClusterer.load(target_dir / "clusterer.joblib")
        ensemble = ClusteredEnsembleModel.load(target_dir / "ensemble.joblib")

        metadata = {}
        meta_file = target_dir / "metadata.json"
        if meta_file.exists():
            with open(meta_file, "r", encoding="utf-8") as f:
                metadata = json.load(f)

        return ModelBundle(
            version=v,
            preprocessor=preprocessor,
            clusterer=clusterer,
            ensemble=ensemble,
            metadata=metadata,
        )

    def list_models(self) -> list[dict[str, Any]]:
        """List all registered models and their evaluation cards."""
        models: list[dict[str, Any]] = []
        active_v = self.get_active_version()

        for item in sorted(self.registry_dir.iterdir(), reverse=True):
            if item.is_dir() and (item / "metadata.json").is_file():
                try:
                    with open(item / "metadata.json", "r", encoding="utf-8") as f:
                        meta = json.load(f)
                        meta["is_active"] = meta.get("version") == active_v
                        models.append(meta)
                except Exception:
                    continue

        return models

    def rollback(self) -> str | None:
        """Roll back to the previously active model version."""
        if not self.pointer_file.exists():
            return None
        with open(self.pointer_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            prev = data.get("previous_version")

        if prev and (self.registry_dir / prev).is_dir():
            self.set_active_version(prev)
            return prev
        return None
