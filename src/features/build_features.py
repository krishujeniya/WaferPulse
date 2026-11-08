"""Feature engineering pipeline entry point (Cookiecutter standard).

Transforms raw or interim data from data/raw or data/interim into
canonical feature matrices saved in data/processed/.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

import click
import pandas as pd

from src.features.preprocessor import TelemetryPreprocessor

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("build_features")


def build_features(
    input_filepath: str | Path,
    output_filepath: str | Path,
    preprocessor_artifact_path: Optional[str | Path] = None,
    null_threshold: float = 0.35,
) -> pd.DataFrame:
    """Read validated interim data, apply preprocessing, and write processed features.

    Args:
        input_filepath: Path to raw or interim CSV.
        output_filepath: Path to save processed feature CSV.
        preprocessor_artifact_path: Optional destination to save serialized preprocessor.
        null_threshold: Column missing threshold for pruning.

    Returns:
        Processed DataFrame.
    """
    in_path = Path(input_filepath)
    out_path = Path(output_filepath)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if in_path.is_file():
        df = pd.read_csv(in_path)
    elif in_path.is_dir():
        files = sorted(list(in_path.glob("*.csv")))
        if not files:
            raise FileNotFoundError(f"No CSV files found in {in_path}")
        df = pd.concat([pd.read_csv(f) for f in files], ignore_index=True)
    else:
        raise FileNotFoundError(f"Input path {in_path} does not exist.")

    logger.info(f"Loaded {len(df)} rows across {len(df.columns)} columns for feature transformation.")

    preprocessor = TelemetryPreprocessor(null_threshold=null_threshold)
    X, y, wafer_ids = preprocessor.fit_transform(df)

    # Reconstruct clean processed DataFrame
    processed_df = pd.DataFrame(X, columns=preprocessor.feature_columns)
    processed_df.insert(0, "Wafer", wafer_ids)
    if y is not None:
        processed_df["Output"] = y

    processed_df.to_csv(out_path, index=False)
    logger.info(f"Saved processed feature matrix ({processed_df.shape}) to {out_path}")

    if preprocessor_artifact_path:
        p_path = Path(preprocessor_artifact_path)
        p_path.parent.mkdir(parents=True, exist_ok=True)
        preprocessor.save(p_path)
        logger.info(f"Saved preprocessor transformer artifact to {p_path}")

    return processed_df


@click.command()
@click.argument("input_filepath", type=click.Path(exists=True), default="data/raw")
@click.argument("output_filepath", type=click.Path(), default="data/processed/features.csv")
@click.option("--preprocessor-path", default="models/preprocessor.joblib", help="Artifact save path")
def main(input_filepath, output_filepath, preprocessor_path):
    """Runs feature extraction and robust scaling pipelines."""
    build_features(input_filepath, output_filepath, preprocessor_path)


if __name__ == "__main__":
    main()
