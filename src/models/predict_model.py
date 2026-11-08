"""Production Inference Engine & Batch Anomaly Scoring.

Loads registered model bundle, executes telemetry preprocessing,
assigns chamber cluster, computes defect probability, and isolates
root-cause sensor deviations for defective wafers.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import Any

import pandas as pd

from src.explain.root_cause import diagnose_single_wafer
from src.models.registry import ModelBundle, ModelRegistry

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("predict_model")


def run_batch_inference(
    input_path: str | Path = "data/prediction",
    output_path: str | Path | None = None,
    model_version: str | None = None,
    registry_dir: str | Path = "models",
) -> dict[str, Any]:
    """Execute batch inference and root-cause analysis on new telemetry file or directory."""
    registry = ModelRegistry(registry_dir=registry_dir)
    bundle: ModelBundle = registry.load_bundle(version=model_version)

    input_p = Path(input_path)
    if input_p.is_file():
        files = [input_p]
    elif input_p.is_dir():
        files = sorted(list(input_p.glob("*.csv")))
    else:
        raise FileNotFoundError(f"Input path {input_p} does not exist.")

    if not files:
        raise FileNotFoundError(f"No CSV files found in {input_p}")

    dfs = [pd.read_csv(f) for f in files]
    df = pd.concat(dfs, ignore_index=True)
    logger.info(f"Loaded {len(df)} wafers for inference from {len(files)} file(s).")

    # Preprocess
    X, _, wafer_ids = bundle.preprocessor.transform(df)

    # Cluster assignment
    clusters = bundle.clusterer.predict(X)

    # Predictions
    preds, probs = bundle.ensemble.predict(X, clusters)

    results: list[dict[str, Any]] = []
    defects_count = 0

    for i in range(len(df)):
        w_id = wafer_ids[i]
        is_def = bool(preds[i] == 1)
        prob = float(probs[i])
        c_id = int(clusters[i])

        if is_def:
            defects_count += 1

        # Extract raw sensor readings for this wafer
        row_dict = df.iloc[i].to_dict()
        diagnosis = diagnose_single_wafer(
            wafer_id=w_id,
            sensor_values=row_dict,
            baseline_stats=bundle.preprocessor.baseline_stats,
            defect_prob=prob,
            cluster_id=c_id,
            top_k=3,
        )

        anom_summary = "; ".join(
            [f"{a.sensor} ({a.direction}, z={a.z_score})" for a in diagnosis.top_anomalies]
        )

        results.append(
            {
                "wafer_id": w_id,
                "cluster_id": c_id,
                "prediction": "Defect" if is_def else "Pass",
                "defect_probability": round(prob, 4),
                "is_defective": is_def,
                "top_anomalous_sensors": anom_summary,
                "detailed_anomalies": [a.to_dict() for a in diagnosis.top_anomalies],
            }
        )

    out_df = pd.DataFrame(
        [
            {
                "Wafer": r["wafer_id"],
                "Cluster": r["cluster_id"],
                "Verdict": r["prediction"],
                "Defect_Probability": r["defect_probability"],
                "Top_Anomalous_Sensors": r["top_anomalous_sensors"],
            }
            for r in results
        ]
    )

    if output_path:
        out_p = Path(output_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        out_df.to_csv(out_p, index=False)
        logger.info(f"Inference output saved to {out_p}")

    summary = {
        "model_version": bundle.version,
        "total_wafers": len(df),
        "defects_detected": defects_count,
        "yield_rate": round((len(df) - defects_count) / max(1, len(df)) * 100.0, 2),
        "results": results,
    }
    return summary


def main():
    parser = argparse.ArgumentParser(description="WaferPulse Batch Inference Engine")
    parser.add_argument("input_path", help="Path to input CSV or directory")
    parser.add_argument("--output", default=None, help="Optional destination path for predictions CSV")
    parser.add_argument("--version", default=None, help="Optional model version to load")
    args = parser.parse_args()

    try:
        run_batch_inference(args.input_path, args.output, args.version)
    except Exception as e:
        logger.error(f"Inference failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
