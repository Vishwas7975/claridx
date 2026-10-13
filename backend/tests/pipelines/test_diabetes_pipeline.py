import numpy as np
import pandas as pd
import pytest

from ml.evaluation import evaluate_on_holdout
from ml.pipelines.diabetes import (
    FEATURES,
    STANDARD_NUMERIC_FEATURES,
    SUSPICIOUS_ZERO_FEATURES,
    build_models,
    build_preprocessor,
)
from tests.pipelines.synthetic import make_diabetes_like_data

MODEL_NAMES = list(build_models(0))


@pytest.mark.parametrize("name", MODEL_NAMES)
def test_model_fits_and_returns_valid_probabilities(name: str) -> None:
    X, y = make_diabetes_like_data(rows=120, seed=0)
    model = build_models(0)[name].fit(X, y)
    proba = model.predict_proba(X)
    assert proba.shape == (len(X), 2)
    assert np.all((proba >= 0) & (proba <= 1))
    assert np.allclose(proba.sum(axis=1), 1.0)


@pytest.mark.parametrize("name", MODEL_NAMES)
def test_prediction_tolerates_missing_inputs(name: str) -> None:
    X, y = make_diabetes_like_data(rows=120, seed=0)
    model = build_models(0)[name].fit(X, y)
    sparse = X.head(5).copy()
    sparse.loc[sparse.index[0], ["plas", "insu", "mass", "preg", "age"]] = np.nan
    proba = model.predict_proba(sparse)
    assert not np.isnan(proba).any()
    assert np.allclose(proba.sum(axis=1), 1.0)


def test_zero_handling_in_preprocessor() -> None:
    """Zero in suspicious columns is imputed to median; zero in preg is preserved."""
    # Construct controlled training frame:
    # plas has non-zero values 100, 200, and one 0. Non-zero median = 150.
    # preg has values 0, 2, 4. Median = 2, but 0 is preserved as 0.
    df = pd.DataFrame(
        {
            "preg": [0.0, 2.0, 4.0],
            "plas": [0.0, 100.0, 200.0],
            "pres": [0.0, 80.0, 90.0],
            "skin": [0.0, 20.0, 40.0],
            "insu": [0.0, 50.0, 150.0],
            "mass": [0.0, 25.0, 35.0],
            "pedi": [0.1, 0.5, 0.9],
            "age": [25.0, 35.0, 45.0],
        }
    )
    preprocessor = build_preprocessor()
    preprocessor.fit(df)

    suspicious_imputer = preprocessor.named_transformers_["suspicious"].named_steps["impute"]
    standard_imputer = preprocessor.named_transformers_["standard"].named_steps["impute"]

    # In suspicious features, 0 was converted to NaN, so medians are of the non-zero values:
    # plas non-zero values are [100, 200] -> median 150.0
    plas_idx = SUSPICIOUS_ZERO_FEATURES.index("plas")
    assert suspicious_imputer.statistics_[plas_idx] == pytest.approx(150.0)

    # In standard features, preg values are [0, 2, 4] -> median is 2.0 (0 was not treated as NaN)
    preg_idx = STANDARD_NUMERIC_FEATURES.index("preg")
    assert standard_imputer.statistics_[preg_idx] == pytest.approx(2.0)


def test_preprocessor_prevents_leakage() -> None:
    """Precomputed training statistics do not change when transforming test data."""
    X_train, _ = make_diabetes_like_data(rows=100, seed=1)
    preprocessor = build_preprocessor().fit(X_train)

    learned_suspicious_medians = (
        preprocessor.named_transformers_["suspicious"].named_steps["impute"].statistics_.copy()
    )
    learned_standard_medians = (
        preprocessor.named_transformers_["standard"].named_steps["impute"].statistics_.copy()
    )

    # Transforming an extreme/adversarial test set does not alter learned statistics:
    adversarial_test = pd.DataFrame({col: [9999.0] * 20 for col in FEATURES})
    preprocessor.transform(adversarial_test)

    current_suspicious_medians = (
        preprocessor.named_transformers_["suspicious"].named_steps["impute"].statistics_
    )
    current_standard_medians = (
        preprocessor.named_transformers_["standard"].named_steps["impute"].statistics_
    )

    np.testing.assert_array_equal(learned_suspicious_medians, current_suspicious_medians)
    np.testing.assert_array_equal(learned_standard_medians, current_standard_medians)


def test_models_are_reproducible() -> None:
    X, y = make_diabetes_like_data(rows=100, seed=42)
    m1 = build_models(seed=42)["random_forest"].fit(X, y)
    m2 = build_models(seed=42)["random_forest"].fit(X, y)

    p1 = m1.predict_proba(X)
    p2 = m2.predict_proba(X)
    np.testing.assert_allclose(p1, p2)


def test_holdout_evaluation_returns_confusion_matrix_and_metrics() -> None:
    X, y = make_diabetes_like_data(rows=100, seed=10)
    model = build_models(seed=10)["logistic_regression"].fit(X[:80], y[:80])
    holdout = evaluate_on_holdout(model, X[80:], y[80:], seed=10)

    expected_keys = {
        "accuracy",
        "precision",
        "recall",
        "f1",
        "roc_auc",
        "roc_auc_ci_low",
        "roc_auc_ci_high",
        "brier",
        "confusion_matrix",
    }
    assert set(holdout) == expected_keys
    cm = holdout["confusion_matrix"]
    assert set(cm) == {"tn", "fp", "fn", "tp"}
    assert cm["tn"] + cm["fp"] + cm["fn"] + cm["tp"] == len(y[80:])
    for val in cm.values():
        assert isinstance(val, int)
        assert val >= 0
