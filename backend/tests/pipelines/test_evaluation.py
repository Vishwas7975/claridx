import numpy as np
import pandas as pd
import pytest
from sklearn.metrics import roc_auc_score

from ml.evaluation import CV_SCORING, bootstrap_auc_ci, cross_validate_model, evaluate_on_holdout
from ml.pipelines.heart import build_models
from tests.pipelines.synthetic import make_heart_like_data


class FixedProbabilities:
    """Returns pre-set probabilities, so metrics can be checked by hand."""

    def __init__(self, positive: list[float]) -> None:
        self._positive = np.array(positive)

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        return np.column_stack([1 - self._positive, self._positive])


def test_bootstrap_ci_collapses_for_perfectly_separated_scores() -> None:
    y = np.array([0] * 30 + [1] * 30)
    proba = np.where(y == 1, 0.9, 0.1)
    assert bootstrap_auc_ci(y, proba, seed=0) == (1.0, 1.0)


def test_bootstrap_ci_brackets_the_point_estimate() -> None:
    rng = np.random.default_rng(1)
    y = rng.integers(0, 2, 300)
    proba = np.clip(0.3 * y + rng.uniform(0, 0.8, 300), 0, 1)
    low, high = bootstrap_auc_ci(y, proba, seed=0)
    assert 0.5 < low < high <= 1.0
    assert low <= roc_auc_score(y, proba) <= high


def test_bootstrap_ci_is_reproducible() -> None:
    rng = np.random.default_rng(2)
    y = rng.integers(0, 2, 120)
    proba = rng.uniform(size=120)
    assert bootstrap_auc_ci(y, proba, seed=7) == bootstrap_auc_ci(y, proba, seed=7)


def test_holdout_metrics_match_hand_computation() -> None:
    # Predictions at 0.5: [1, 0, 1, 0] against truth [1, 1, 0, 0]: one hit, one miss of each kind.
    model = FixedProbabilities([0.9, 0.4, 0.6, 0.1])
    X_test = pd.DataFrame({"unused": range(4)})
    y_test = pd.Series([1, 1, 0, 0])
    result = evaluate_on_holdout(model, X_test, y_test, seed=0)

    assert result["accuracy"] == pytest.approx(0.5)
    assert result["precision"] == pytest.approx(0.5)
    assert result["recall"] == pytest.approx(0.5)
    assert result["f1"] == pytest.approx(0.5)
    assert result["roc_auc"] == pytest.approx(0.75)  # 3 of 4 positive/negative pairs ranked right
    assert result["brier"] == pytest.approx(0.185)  # (0.01 + 0.36 + 0.36 + 0.01) / 4
    assert result["confusion_matrix"] == {"tn": 1, "fp": 1, "fn": 1, "tp": 1}
    assert 0.0 <= result["roc_auc_ci_low"] <= result["roc_auc_ci_high"] <= 1.0


def test_cross_validation_reports_every_metric_with_sane_values() -> None:
    X, y = make_heart_like_data()
    summary = cross_validate_model(build_models(0)["logistic_regression"], X, y, seed=0)

    assert set(summary) == set(CV_SCORING)
    for mean, std in summary.values():
        assert 0.0 <= mean <= 1.0
        assert std >= 0.0
    assert summary["roc_auc"][0] > 0.7
    assert summary["brier"][0] > 0.0  # the loss is reported as a positive number
