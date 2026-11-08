.PHONY: clean data features train predict visualize test lint run-backend run-frontend build-frontend help

PROJECT_DIR := $(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))
PYTHON_INTERPRETER = python3

help:
	@echo "WaferGuard - Cookiecutter MLOps & Data Science Automation:"
	@echo "  make data            Ingest and validate raw sensor batches -> data/interim"
	@echo "  make features        Extract and scale features -> data/processed"
	@echo "  make train           Fit chamber K-Means clusters & train ensemble models -> models/"
	@echo "  make predict         Score batch wafer files -> reports/"
	@echo "  make visualize       Generate wafer topography & drift figures -> reports/figures/"
	@echo "  make test            Execute pytest test ratchet suite"
	@echo "  make lint            Run ruff/flake8 syntax and quality checks"
	@echo "  make run-backend     Launch production FastAPI backend on port 8000"
	@echo "  make run-frontend    Launch Vite React telemetry dashboard on port 3000"
	@echo "  make build-frontend  Build production frontend bundle into frontend/dist"
	@echo "  make clean           Delete temporary artifacts, bytecode, and test caches"

data:
	PYTHONPATH=. $(PYTHON_INTERPRETER) src/data/make_dataset.py data/raw data/interim/clean_telemetry.csv

features:
	PYTHONPATH=. $(PYTHON_INTERPRETER) src/features/build_features.py data/interim/clean_telemetry.csv data/processed/features.csv --preprocessor-path models/preprocessor.joblib

train:
	PYTHONPATH=. $(PYTHON_INTERPRETER) src/models/train_model.py --data-dir data/raw --registry-dir models

predict:
	PYTHONPATH=. $(PYTHON_INTERPRETER) src/models/predict_model.py data/prediction/ --output reports/batch_predictions.csv --registry-dir models

visualize:
	PYTHONPATH=. $(PYTHON_INTERPRETER) src/visualization/visualize.py

test:
	PYTHONPATH=. $(PYTHON_INTERPRETER) -m pytest tests/ -v

lint:
	.venv/bin/ruff check --select E,F --ignore E501 src backend

run-backend:
	PYTHONPATH=. uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload

run-frontend:
	cd frontend && bun run dev

build-frontend:
	cd frontend && bun run build

clean:
	find . -type f -name "*.py[co]" -delete
	find . -type d -name "__pycache__" -delete
	rm -rf .pytest_cache
