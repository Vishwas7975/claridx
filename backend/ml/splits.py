"""The one deterministic train/test split shared by training and explanation code."""

import pandas as pd
from sklearn.model_selection import train_test_split

from ml.config import RANDOM_SEED, TEST_SIZE
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
