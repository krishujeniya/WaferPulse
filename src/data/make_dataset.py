"""Dataset processing script (Cookiecutter Data Science standard).

Turns raw data from (data/raw or Training_Batch_Files) into validated,
clean data ready for feature engineering (saved in data/interim/).
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import List

import click
import pandas as pd

try:
    from dotenv import find_dotenv, load_dotenv
except ImportError:
    find_dotenv = lambda: None  # noqa: E731
    load_dotenv = lambda *args, **kwargs: None  # noqa: E731

from src.data.generator import generate_batch_files
from src.data.validator import TelemetryValidator

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("make_dataset")


def make_dataset(
    input_filepath: str | Path = "data/raw",
    output_filepath: str | Path = "data/interim/clean_telemetry.csv",
    auto_generate_if_missing: bool = True,
) -> pd.DataFrame:
    """Ingest, validate, and clean raw wafer telemetry batches.

    Args:
        input_filepath: Path to raw CSV file or directory containing batches.
        output_filepath: Destination CSV for validated interim dataset.
        auto_generate_if_missing: If no files exist, generate realistic sample batches.

    Returns:
        Validated combined DataFrame.
    """
    in_path = Path(input_filepath)
    out_path = Path(output_filepath)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # If data/raw has no CSVs, check if Training_Batch_Files has them, or generate
    csv_files = []
    if in_path.is_file():
        csv_files = [in_path]
    elif in_path.is_dir():
        csv_files = sorted(list(in_path.glob("*.csv")))

    if not csv_files:
        alt_path = Path("Training_Batch_Files")
        if alt_path.is_dir():
            csv_files = sorted(list(alt_path.glob("*.csv")))

    if not csv_files and auto_generate_if_missing:
        logger.info(f"No CSVs found in {in_path}; generating synthetic baseline telemetry batches...")
        in_path.mkdir(parents=True, exist_ok=True)
        csv_files = generate_batch_files(
            output_dir=in_path,
            num_files=3,
            samples_per_file=150,
            num_sensors=60,
            is_training=True,
            random_state_start=42,
        )

    if not csv_files:
        raise FileNotFoundError(f"No telemetry CSV files found in {in_path}")

    logger.info(f"Validating {len(csv_files)} batch file(s) from {in_path}...")
    validator = TelemetryValidator()
    quarantine_dir = in_path.parent / "quarantine"
    valid_dfs: List[pd.DataFrame] = []

    for f in csv_files:
        report = validator.validate_file(f, is_training=True, quarantine_dir=quarantine_dir)
        if report.is_valid:
            valid_dfs.append(pd.read_csv(f))
            logger.info(f"Validated {f.name}: {report.row_count} wafers, {report.column_count} cols")
        else:
            logger.warning(f"Batch quarantined: {f.name} - {report.quarantine_reason}")

    if not valid_dfs:
        raise ValueError("All raw batch files failed schema validation.")

    combined_df = pd.concat(valid_dfs, ignore_index=True)
    combined_df.to_csv(out_path, index=False)
    logger.info(f"Saved {len(combined_df)} validated wafer records to {out_path}")

    return combined_df


@click.command()
@click.argument("input_filepath", type=click.Path(exists=True), default="data/raw")
@click.argument("output_filepath", type=click.Path(), default="data/interim/clean_telemetry.csv")
def main(input_filepath, output_filepath):
    """Runs data processing scripts to turn raw data into cleaned interim data."""
    load_dotenv(find_dotenv())
    make_dataset(input_filepath, output_filepath)


if __name__ == "__main__":
    main()
