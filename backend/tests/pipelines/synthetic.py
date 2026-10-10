"""Synthetic heart-like data with a learnable signal, for tests that need fitted models."""

import numpy as np
import pandas as pd

from ml.pipelines.heart import FEATURES


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
    return frame[FEATURES], target
