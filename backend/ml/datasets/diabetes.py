"""Pima Indians Diabetes dataset (OpenML ID 37): download and load."""

from pathlib import Path

import pandas as pd
from sklearn.datasets import fetch_openml

from ml.datasets.heart import sha256_of as sha256_of
from ml.paths import RAW_DATA_DIR

OPENML_DATASET_ID = 37
RAW_FILE = RAW_DATA_DIR / "diabetes_openml37.csv"

# Raw target: categorical "tested_positive" / "tested_negative".
TARGET_RAW = "class"

# Explicit ordered feature list (all numeric).
FEATURES = ["preg", "plas", "pres", "skin", "insu", "mass", "pedi", "age"]

# Columns where 0 is physiologically impossible and represents missing data.
# The raw loader keeps zeros as-is; conversion belongs to the pipeline.
ZERO_AS_MISSING = ["plas", "pres", "skin", "insu", "mass"]

EXPECTED_COLUMNS = set(FEATURES + [TARGET_RAW])
VALID_TARGETS = {"tested_negative", "tested_positive"}


def download(force: bool = False) -> Path:
    """Fetch the dataset from OpenML and store it as one CSV."""
    if RAW_FILE.exists() and not force:
        return RAW_FILE

    bunch = fetch_openml(data_id=OPENML_DATASET_ID, as_frame=True, parser="auto")
    frame = bunch.frame

    # Validate schema before saving.
    _validate_schema(frame)

    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    frame.to_csv(RAW_FILE, index=False)
    return RAW_FILE


def load_raw() -> pd.DataFrame:
    """Load the cached CSV and validate its schema."""
    if not RAW_FILE.exists():
        raise FileNotFoundError(
            "Dataset missing. Run: uv run python -m ml.scripts.download_diabetes"
        )
    frame = pd.read_csv(RAW_FILE)
    _validate_schema(frame)
    return frame


def _validate_schema(frame: pd.DataFrame) -> None:
    """Fail fast on unexpected columns or target labels."""
    actual_cols = set(frame.columns)
    if actual_cols != EXPECTED_COLUMNS:
        missing = sorted(EXPECTED_COLUMNS - actual_cols)
        extra = sorted(actual_cols - EXPECTED_COLUMNS)
        raise ValueError(f"Unexpected schema. Missing: {missing}, Extra: {extra}")

    if TARGET_RAW not in frame.columns:
        raise ValueError(f"Target column '{TARGET_RAW}' not found.")

    actual_targets = set(frame[TARGET_RAW].dropna().unique())
    if not actual_targets <= VALID_TARGETS:
        raise ValueError(f"Invalid target labels: {sorted(actual_targets - VALID_TARGETS)}")
