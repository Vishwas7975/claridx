"""The one deterministic train/test split shared by training and explanation code."""

import pandas as pd
from sklearn.model_selection import train_test_split

from ml.config import RANDOM_SEED, TEST_SIZE
from ml.datasets.diabetes import (
    EXPECTED_COLUMNS as DIABETES_EXPECTED_COLUMNS,
)
from ml.datasets.diabetes import (
    FEATURES as DIABETES_FEATURES,
)
from ml.datasets.diabetes import (
    TARGET_RAW as DIABETES_TARGET_RAW,
)
from ml.datasets.diabetes import (
    VALID_TARGETS as DIABETES_VALID_TARGETS,
)
from ml.datasets.diabetes import (
    load_raw as load_diabetes_raw,
)
from ml.datasets.heart import TARGET_RAW, load_raw
from ml.pipelines.heart import FEATURES


def heart_split() -> tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    """Return X_train, X_test, y_train, y_test (stratified, seeded)."""
    df = load_raw()
    X = df[FEATURES]
    y = (df[TARGET_RAW] > 0).astype(int)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, stratify=y, random_state=RANDOM_SEED
    )
    return X_train, X_test, y_train, y_test


def diabetes_split() -> tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    """Return X_train, X_test, y_train, y_test (stratified, seeded) for diabetes."""
    df = load_diabetes_raw()
    actual_cols = set(df.columns)
    if actual_cols != DIABETES_EXPECTED_COLUMNS:
        missing = sorted(DIABETES_EXPECTED_COLUMNS - actual_cols)
        extra = sorted(actual_cols - DIABETES_EXPECTED_COLUMNS)
        raise ValueError(f"Unexpected schema in diabetes split. Missing: {missing}, Extra: {extra}")

    actual_targets = set(df[DIABETES_TARGET_RAW].dropna().unique())
    if not actual_targets <= DIABETES_VALID_TARGETS:
        raise ValueError(
            f"Invalid target labels: {sorted(actual_targets - DIABETES_VALID_TARGETS)}"
        )

    X = df[DIABETES_FEATURES]
    y = (df[DIABETES_TARGET_RAW] == "tested_positive").astype(int)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, stratify=y, random_state=RANDOM_SEED
    )
    return X_train, X_test, y_train, y_test
