from itertools import product

import numpy as np
import pandas as pd
import pytest

from ml.pipelines.heart import build_models
from ml.sensitivity import SensitivityAnalyzer
from tests.pipelines.synthetic import make_heart_like_data


class ThalStub:
    """Predicts disease only when thal is 7 and ignores every other feature."""

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        positive = np.where(X["thal"].fillna(3.0).to_numpy() == 7, 0.9, 0.1)
        return np.column_stack([1 - positive, positive])


@pytest.fixture(scope="module")
def data():
    return make_heart_like_data()


@pytest.fixture(scope="module")
def forest(data):
    X, y = data
    return build_models(0)["random_forest"].fit(X, y)


def _probability(model, patient: pd.DataFrame, **values: float) -> float:
    row = patient.copy()
    for name, value in values.items():
        row[name] = value
    return float(model.predict_proba(row)[0, 1])


def test_no_missing_values_means_no_sensitivity(forest, data) -> None:
    X, _ = data
    assert SensitivityAnalyzer(forest, X).analyze(X.iloc[[0]]) is None


def test_verdict_flip_detected_when_decisive_feature_is_missing(data) -> None:
    X, _ = data
    patient = X.iloc[[0]].copy()
    patient["thal"] = np.nan
    result = SensitivityAnalyzer(ThalStub(), X).analyze(patient)

    assert result is not None
    assert result.can_flip is True
    assert result.baseline_probability == pytest.approx(0.1)
    assert result.probability_min == pytest.approx(0.1)
    assert result.probability_max == pytest.approx(0.9)
    assert result.impacts[0].feature == "thal"
    assert result.impacts[0].can_flip is True


def test_no_flip_when_missing_feature_does_not_matter(data) -> None:
    X, _ = data
    patient = X.iloc[[0]].copy()
    patient["thal"] = 3.0
    patient["chol"] = np.nan
    result = SensitivityAnalyzer(ThalStub(), X).analyze(patient)

    assert result is not None
    assert result.can_flip is False
    assert result.impacts[0].spread == pytest.approx(0.0)


def test_exhaustive_range_matches_brute_force(forest, data) -> None:
    X, _ = data
    patient = X.iloc[[3]].copy()
    patient["thal"] = np.nan
    patient["ca"] = np.nan

    thals = sorted(X["thal"].unique())
    cas = sorted(X["ca"].unique())
    expected = [_probability(forest, patient)]  # baseline
    expected += [_probability(forest, patient, thal=t, ca=c) for t, c in product(thals, cas)]
    expected += [_probability(forest, patient, thal=t) for t in thals]
    expected += [_probability(forest, patient, ca=c) for c in cas]

    result = SensitivityAnalyzer(forest, X).analyze(patient)
    assert result is not None
    assert result.exhaustive is True
    assert result.probability_min == pytest.approx(min(expected))
    assert result.probability_max == pytest.approx(max(expected))


@pytest.mark.parametrize("name", ["random_forest", "logistic_regression"])
def test_baseline_lies_inside_range(name: str, data) -> None:
    X, y = data
    model = build_models(0)[name].fit(X, y)
    patient = X.iloc[[5]].copy()
    patient["chol"] = np.nan
    patient["ca"] = np.nan
    result = SensitivityAnalyzer(model, X).analyze(patient)

    assert result is not None
    assert result.probability_min <= result.baseline_probability <= result.probability_max


def test_large_search_space_is_sampled_deterministically(forest, data) -> None:
    X, _ = data
    patient = X.iloc[[0]].copy()
    for name in ("age", "trestbps", "chol", "thalach", "oldpeak", "cp"):
        patient[name] = np.nan

    analyzer = SensitivityAnalyzer(forest, X, max_scenarios=200)
    first = analyzer.analyze(patient)
    second = analyzer.analyze(patient)

    assert first is not None
    assert first.exhaustive is False
    assert 200 < first.scenarios_evaluated <= 230  # 200 joint + at most 29 single-feature rows
    assert first == second


def test_impacts_cover_missing_features_sorted_by_spread(forest, data) -> None:
    X, _ = data
    patient = X.iloc[[1]].copy()
    missing = ["chol", "thal", "ca", "slope"]
    for name in missing:
        patient[name] = np.nan

    result = SensitivityAnalyzer(forest, X).analyze(patient)
    assert result is not None
    assert {impact.feature for impact in result.impacts} == set(missing)
    spreads = [impact.spread for impact in result.impacts]
    assert spreads == sorted(spreads, reverse=True)
