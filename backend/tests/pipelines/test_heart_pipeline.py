import numpy as np
import pandas as pd
import pytest

from ml.pipelines.heart import FEATURES, build_models

MODEL_NAMES = list(build_models(0))


def _synthetic_data(rows: int = 120, seed: int = 0) -> tuple[pd.DataFrame, pd.Series]:
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
    target = pd.Series(np.arange(rows) % 2)  # guarantees both classes
    return frame[FEATURES], target


@pytest.mark.parametrize("name", MODEL_NAMES)
def test_model_fits_and_returns_valid_probabilities(name: str) -> None:
    X, y = _synthetic_data()
    model = build_models(0)[name].fit(X, y)
    proba = model.predict_proba(X)
    assert proba.shape == (len(X), 2)
    assert np.all((proba >= 0) & (proba <= 1))
    assert np.allclose(proba.sum(axis=1), 1.0)


@pytest.mark.parametrize("name", MODEL_NAMES)
def test_prediction_tolerates_missing_inputs(name: str) -> None:
    X, y = _synthetic_data()
    model = build_models(0)[name].fit(X, y)
    sparse = X.head(5).copy()
    sparse.loc[sparse.index[0], ["ca", "thal", "chol", "sex"]] = np.nan
    proba = model.predict_proba(sparse)
    assert not np.isnan(proba).any()


@pytest.mark.parametrize("name", MODEL_NAMES)
def test_prediction_tolerates_unseen_category(name: str) -> None:
    X, y = _synthetic_data()
    model = build_models(0)[name].fit(X, y)
    odd = X.head(3).copy()
    odd["cp"] = 9
    odd["thal"] = 5.0
    assert not np.isnan(model.predict_proba(odd)).any()
