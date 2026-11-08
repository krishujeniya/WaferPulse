# AI Handoff - Cookiecutter MLOps & Data Science Architecture

## Task
Aligned and organized WaferGuard strictly according to standard Cookiecutter Data Science (CCDS) and Cookiecutter MLOps structure:
- Structured `data/` hierarchy: `data/raw/`, `data/interim/`, `data/processed/`, `data/prediction/`, `data/quarantine/`, `data/external/`.
- Implemented `src/data/make_dataset.py` to ingest and validate raw batches into `data/interim/clean_telemetry.csv`.
- Implemented `src/features/build_features.py` to transform interim data into scaled feature matrices in `data/processed/features.csv`.
- Implemented `src/visualization/visualize.py` to output silicon wafer topography die maps and sensor drift reports into `reports/figures/`.
- Re-homed model registry and serialized artifacts into `models/` per CCDS convention.
- Added exploratory analysis notebook `notebooks/1.0-wafer-sensor-exploratory-analysis.ipynb`.
- Added telemetry data dictionary `references/data_dictionary.md`.
- Exposed `src/api/` as a native Cookiecutter MLOps API module.
- Standardized `Makefile` targets: `make data`, `make features`, `make train`, `make predict`, `make visualize`, `make test`, `make lint`.

## Branch & Revision
- Branch: `main`

## Verification Evidence
- `make data`: 760 records validated and written to `data/interim/clean_telemetry.csv`.
- `make features`: 760 rows x 62 columns processed into `data/processed/features.csv` and `models/preprocessor.joblib`.
- `make visualize`: `reports/figures/wafer_die_map.svg` and `reports/figures/sensor_drift_report.svg` generated.
- `make test`: 15 passed across `test_api.py`, `test_ml_pipeline.py`, and `test_cookiecutter_pipeline.py`.
- `make lint`: Clean pass (0 syntax or import errors).

## Next Authorized Command
```bash
make test
```
