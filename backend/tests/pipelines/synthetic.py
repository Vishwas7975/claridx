"""Synthetic data with learnable signals for tests that need fitted models."""

import numpy as np
import pandas as pd

from ml.datasets.diabetes import FEATURES as DIABETES_FEATURES
from ml.pipelines.heart import FEATURES as HEART_FEATURES


def make_heart_like_data(rows: int = 160, seed: int = 0) -> tuple[pd.DataFrame, pd.Series]:
    rng = np.random.default_rng(seed)
    frame = pd.DataFrame(
        {
            "age": rng.integers(30, 80, rows),
            "trestbps": rng.integers(95, 200, rows),
            "chol": rng.integers(130, 560, rows),
            "thalach": rng.integers(70, 200, rows),
            "oldpeak": rng.uniform(0, 6, rows),
            "ca": rng.integers(0, 4, rows).astype(float),
            "cp": rng.integers(1, 5, rows),
            "restecg": rng.integers(0, 3, rows),
            "slope": rng.integers(1, 4, rows),
            "thal": rng.choice([3.0, 6.0, 7.0], rows),
            "sex": rng.integers(0, 2, rows),
            "fbs": rng.integers(0, 2, rows),
            "exang": rng.integers(0, 2, rows),
        }
    )
    score = frame["oldpeak"] + frame["ca"] + 1.5 * (frame["thal"] == 7) + rng.normal(0, 1, rows)
    target = pd.Series((score > np.median(score)).astype(int))
    return frame[HEART_FEATURES], target


def make_diabetes_like_data(rows: int = 160, seed: int = 0) -> tuple[pd.DataFrame, pd.Series]:
    """Generate synthetic diabetes data with the 8 expected numeric features and zero values."""
    rng = np.random.default_rng(seed)

    plas = rng.integers(50, 200, rows)
    pres = rng.integers(40, 120, rows)
    skin = rng.integers(10, 60, rows)
    insu = rng.integers(15, 600, rows)
    mass = rng.uniform(18.0, 55.0, rows).round(1)

    # Inject realistic zeros into suspicious columns
    plas[rng.choice(rows, size=max(1, int(rows * 0.01)), replace=False)] = 0
    pres[rng.choice(rows, size=max(1, int(rows * 0.05)), replace=False)] = 0
    skin[rng.choice(rows, size=max(1, int(rows * 0.30)), replace=False)] = 0
    insu[rng.choice(rows, size=max(1, int(rows * 0.45)), replace=False)] = 0
    mass[rng.choice(rows, size=max(1, int(rows * 0.02)), replace=False)] = 0.0

    frame = pd.DataFrame(
        {
            "preg": rng.integers(0, 15, rows),
            "plas": plas,
            "pres": pres,
            "skin": skin,
            "insu": insu,
            "mass": mass,
            "pedi": rng.uniform(0.08, 2.4, rows).round(3),
            "age": rng.integers(21, 80, rows),
        }
    )

    score = (
        (frame["plas"] > 140).astype(float) * 2.0
        + (frame["mass"] > 30.0).astype(float) * 1.5
        + (frame["age"] > 40).astype(float) * 1.0
        + rng.normal(0, 1, rows)
    )
    target = pd.Series((score > np.median(score)).astype(int))
    return frame[DIABETES_FEATURES], target
