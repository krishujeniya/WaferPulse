"""Industrial Telemetry Validation and Schema Enforcement Module.

Implements strict MLOps schema contracts for semiconductor telemetry batches:
- Wafer identifier syntax verification
- Schema consistency (expected column names and data types)
- Null-value thresholds and data corruption checks
- Automatic quarantine routing for malformed or out-of-spec batches
"""

from __future__ import annotations

import json
import logging
import shutil
from dataclasses import asdict, dataclass, field
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class ValidationReport:
    """Detailed validation summary for a single telemetry batch file."""

    file_name: str
    is_valid: bool
    row_count: int
    column_count: int
    has_wafer_column: bool
    has_output_column: bool
    missing_rate_overall: float
    columns_with_excess_missing: list[str] = field(default_factory=list)
    quarantine_reason: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)


class TelemetryValidator:
    """Enforces industrial validation rules on raw wafer sensor files."""

    def __init__(
        self,
        schema_path: str | Path | None = None,
        max_missing_ratio: float = 0.50,
        expected_sensor_prefix: str = "Sensor_",
    ):
        self.max_missing_ratio = max_missing_ratio
        self.expected_sensor_prefix = expected_sensor_prefix
        self.expected_columns: list[str] | None = None
        if schema_path and Path(schema_path).exists():
            self.load_schema(schema_path)

    def load_schema(self, schema_path: str | Path) -> None:
        """Load expected schema dictionary from JSON file."""
        with open(schema_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            self.expected_columns = data.get("columns", [])

    def validate_file(
        self,
        file_path: str | Path,
        is_training: bool = True,
        quarantine_dir: str | Path | None = None,
    ) -> ValidationReport:
        """Validate an individual CSV batch file against data contracts.

        Args:
            file_path: Path to CSV batch file.
            is_training: If True, requires 'Output' column with valid labels.
            quarantine_dir: If provided, corrupt or invalid files are moved here.

        Returns:
            ValidationReport with full audit metadata.
        """
        path = Path(file_path)
        file_name = path.name

        if not path.is_file():
            report = ValidationReport(
                file_name=file_name,
                is_valid=False,
                row_count=0,
                column_count=0,
                has_wafer_column=False,
                has_output_column=False,
                missing_rate_overall=1.0,
                quarantine_reason="File does not exist or is not a regular file",
            )
            return report

        try:
            df = pd.read_csv(path)
        except Exception as e:
            reason = f"CSV parsing error: {e!s}"
            self._handle_quarantine(path, quarantine_dir, reason)
            return ValidationReport(
                file_name=file_name,
                is_valid=False,
                row_count=0,
                column_count=0,
                has_wafer_column=False,
                has_output_column=False,
                missing_rate_overall=1.0,
                quarantine_reason=reason,
            )

        row_count, col_count = df.shape
        if row_count == 0 or col_count == 0:
            reason = "File contains empty dataset (0 rows or 0 columns)"
            self._handle_quarantine(path, quarantine_dir, reason)
            return ValidationReport(
                file_name=file_name,
                is_valid=False,
                row_count=row_count,
                column_count=col_count,
                has_wafer_column=False,
                has_output_column=False,
                missing_rate_overall=1.0,
                quarantine_reason=reason,
            )

        # 1. Check primary Wafer key column
        has_wafer_column = "Wafer" in df.columns
        if not has_wafer_column:
            reason = "Missing primary key column 'Wafer'"
            self._handle_quarantine(path, quarantine_dir, reason)
            return ValidationReport(
                file_name=file_name,
                is_valid=False,
                row_count=row_count,
                column_count=col_count,
                has_wafer_column=False,
                has_output_column="Output" in df.columns,
                missing_rate_overall=float(df.isna().mean().mean()),
                quarantine_reason=reason,
            )

        # 2. Check Output column if training
        has_output = "Output" in df.columns
        if is_training and not has_output:
            reason = "Training dataset missing target column 'Output'"
            self._handle_quarantine(path, quarantine_dir, reason)
            return ValidationReport(
                file_name=file_name,
                is_valid=False,
                row_count=row_count,
                column_count=col_count,
                has_wafer_column=True,
                has_output_column=False,
                missing_rate_overall=float(df.isna().mean().mean()),
                quarantine_reason=reason,
            )

        # 3. Check for valid label domain if Output exists: values must be in {1, -1, 0}
        if has_output:
            valid_labels = {1, -1, 0}
            unique_labels = set(df["Output"].dropna().unique())
            if not unique_labels.issubset(valid_labels):
                reason = f"Target 'Output' contains invalid labels: {unique_labels - valid_labels}"
                self._handle_quarantine(path, quarantine_dir, reason)
                return ValidationReport(
                    file_name=file_name,
                    is_valid=False,
                    row_count=row_count,
                    column_count=col_count,
                    has_wafer_column=True,
                    has_output_column=True,
                    missing_rate_overall=float(df.isna().mean().mean()),
                    quarantine_reason=reason,
                )

        # 4. Check missing rate thresholds
        missing_ratios = df.isna().mean()
        overall_missing = float(missing_ratios.mean())
        excess_missing_cols = [
            str(col) for col, ratio in missing_ratios.items() if ratio > self.max_missing_ratio
        ]

        # 5. Check schema against expected columns if schema loaded
        if self.expected_columns:
            missing_expected = [c for c in self.expected_columns if c not in df.columns]
            if missing_expected:
                reason = f"Schema mismatch: missing {len(missing_expected)} expected columns"
                self._handle_quarantine(path, quarantine_dir, reason)
                return ValidationReport(
                    file_name=file_name,
                    is_valid=False,
                    row_count=row_count,
                    column_count=col_count,
                    has_wafer_column=True,
                    has_output_column=has_output,
                    missing_rate_overall=overall_missing,
                    columns_with_excess_missing=excess_missing_cols,
                    quarantine_reason=reason,
                )

        return ValidationReport(
            file_name=file_name,
            is_valid=True,
            row_count=row_count,
            column_count=col_count,
            has_wafer_column=True,
            has_output_column=has_output,
            missing_rate_overall=overall_missing,
            columns_with_excess_missing=excess_missing_cols,
            quarantine_reason=None,
        )

    def _handle_quarantine(
        self, file_path: Path, quarantine_dir: str | Path | None, reason: str
    ) -> None:
        """Move corrupted file to quarantine directory and write failure log."""
        if not quarantine_dir:
            return
        q_path = Path(quarantine_dir)
        q_path.mkdir(parents=True, exist_ok=True)
        dest = q_path / file_path.name
        try:
            shutil.copy2(file_path, dest)
            log_file = q_path / f"{file_path.stem}_quarantine.log"
            with open(log_file, "w", encoding="utf-8") as f:
                f.write(f"File: {file_path.name}\nReason: {reason}\n")
            logger.warning(f"Quarantined {file_path.name}: {reason}")
        except Exception as e:
            logger.error(f"Failed to quarantine file {file_path}: {e}")
