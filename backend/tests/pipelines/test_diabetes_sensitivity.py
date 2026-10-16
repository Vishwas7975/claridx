"""Unit tests for diabetes missing-data sensitivity analysis."""

import numpy as np
import pandas as pd
import pytest

from ml.pipelines.diabetes import (
    FEATURES,
    SUSPICIOUS_ZERO_FEATURES,
    build_models,
)
from ml.sensitivity import SensitivityAnalyzer
from tests.pipelines.synthetic import make_diabetes_like_data


class SyntheticDiabetesModel:
    """Predicts disease if insulin > 150, otherwise normal."""

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        positive = np.where(X["insu"] > 150.0, 0.85, 0.15)
        return np.column_stack([1 - positive, positive])


@pytest.fixture(scope="module")
def diabetes_data():
    return make_diabetes_like_data()


@pytest.fixture(scope="module")
def logistic(diabetes_data):
    X, y = diabetes_data
    return build_models(0)["logistic_regression"].fit(X, y)


@pytest.fixture(scope="module")
def forest(diabetes_data):
    X, y = diabetes_data
    return build_models(0)["random_forest"].fit(X, y)


def _analyzer(model, background, threshold: float = 0.5) -> SensitivityAnalyzer:
    return SensitivityAnalyzer(
        model=model,
        background=background,
        features=FEATURES,
        zero_as_missing=SUSPICIOUS_ZERO_FEATURES,
        threshold=threshold,
    )


def test_complete_measurements_means_no_sensitivity(logistic, diabetes_data) -> None:
    X, _ = diabetes_data
    patient = X.iloc[[0]].copy()
    # Ensure patient has valid non-zero values for all suspicious features
    for col in SUSPICIOUS_ZERO_FEATURES:
        patient[col] = 50.0
    patient["preg"] = 2
    assert _analyzer(logistic, X).analyze(patient) is None


def test_preg_zero_is_valid_and_does_not_trigger_sensitivity(logistic, diabetes_data) -> None:
    X, _ = diabetes_data
    patient = X.iloc[[0]].copy()
    for col in SUSPICIOUS_ZERO_FEATURES:
        patient[col] = 50.0
    patient["preg"] = 0
    assert _analyzer(logistic, X).analyze(patient) is None


def test_suspicious_zeros_treated_as_missing(logistic, diabetes_data) -> None:
    X, _ = diabetes_data
    patient = X.iloc[[0]].copy()
    for col in SUSPICIOUS_ZERO_FEATURES:
        patient[col] = 50.0
    patient["skin"] = 0.0
    patient["insu"] = 0.0

    result = _analyzer(logistic, X).analyze(patient)
    assert result is not None
    assert {impact.feature for impact in result.impacts} == {"skin", "insu"}
    assert result.patterns_used > 0


def test_nan_and_suspicious_zero_produce_identical_results(logistic, diabetes_data) -> None:
    X, _ = diabetes_data
    patient_zero = X.iloc[[0]].copy()
    patient_nan = X.iloc[[0]].copy()
    for col in SUSPICIOUS_ZERO_FEATURES:
        patient_zero[col] = 50.0
        patient_nan[col] = 50.0

    patient_zero["skin"] = 0.0
    patient_zero["insu"] = 0.0

    patient_nan["skin"] = np.nan
    patient_nan["insu"] = np.nan

    analyzer = _analyzer(logistic, X)
    res_zero = analyzer.analyze(patient_zero)
    res_nan = analyzer.analyze(patient_nan)

    assert res_zero is not None and res_nan is not None
    assert res_zero.baseline_probability == pytest.approx(res_nan.baseline_probability)
    assert res_zero.positive_share == pytest.approx(res_nan.positive_share)
    assert res_zero.typical_low == pytest.approx(res_nan.typical_low)
    assert res_zero.typical_high == pytest.approx(res_nan.typical_high)
    assert res_zero.patterns_used == res_nan.patterns_used
    assert res_zero.verdict_uncertain == res_nan.verdict_uncertain


def test_uncertain_verdict_when_positive_share_between_10_and_90_percent(diabetes_data) -> None:
    X, _ = diabetes_data
    background = X.copy()
    # 40% high insulin, 60% low insulin
    n = len(background)
    cutoff = int(0.4 * n)
    background.iloc[:cutoff, background.columns.get_loc("insu")] = 250.0
    background.iloc[cutoff:, background.columns.get_loc("insu")] = 50.0

    patient = X.iloc[[0]].copy()
    patient["insu"] = np.nan

    result = _analyzer(SyntheticDiabetesModel(), background).analyze(patient)
    assert result is not None
    assert result.positive_share == pytest.approx(0.4)
    assert result.verdict_uncertain is True
    assert result.impacts[0].can_flip is True


def test_stable_verdict_when_positive_share_below_10_percent(diabetes_data) -> None:
    X, _ = diabetes_data
    background = X.copy()
    background["insu"] = 50.0  # all below threshold

    patient = X.iloc[[0]].copy()
    patient["insu"] = np.nan

    result = _analyzer(SyntheticDiabetesModel(), background).analyze(patient)
    assert result is not None
    assert result.positive_share == pytest.approx(0.0)
    assert result.verdict_uncertain is False
    assert result.impacts[0].can_flip is False


def test_empty_background_returns_none(logistic, diabetes_data) -> None:
    X, _ = diabetes_data
    empty_bg = pd.DataFrame(columns=FEATURES)
    patient = X.iloc[[0]].copy()
    patient["skin"] = np.nan

    assert _analyzer(logistic, empty_bg).analyze(patient) is None


def test_no_training_patient_with_all_missing_features_returns_none(
    logistic, diabetes_data
) -> None:
    X, _ = diabetes_data
    bg = X.copy()
    # Ensure no patient has both skin and insu non-zero
    half = len(bg) // 2
    bg.iloc[:half, bg.columns.get_loc("skin")] = 0.0
    bg.iloc[half:, bg.columns.get_loc("insu")] = 0.0

    patient = X.iloc[[0]].copy()
    patient["skin"] = np.nan
    patient["insu"] = np.nan

    assert _analyzer(logistic, bg).analyze(patient) is None


@pytest.mark.parametrize("name", ["random_forest", "logistic_regression"])
def test_ranges_are_nested_and_contain_baseline(name: str, diabetes_data) -> None:
    X, y = diabetes_data
    model = build_models(0)[name].fit(X, y)
    patient = X.iloc[[0]].copy()
    patient["skin"] = np.nan
    patient["insu"] = np.nan

    result = _analyzer(model, X).analyze(patient)
    assert result is not None
    assert result.probability_min <= result.typical_low <= result.typical_high
    assert result.typical_high <= result.probability_max
    assert result.probability_min <= result.baseline_probability <= result.probability_max
    assert 0.0 <= result.positive_share <= 1.0


def test_impacts_cover_missing_features_sorted_by_spread(forest, diabetes_data) -> None:
    X, _ = diabetes_data
    patient = X.iloc[[0]].copy()
    missing = ["skin", "insu", "mass"]
    for col in missing:
        patient[col] = np.nan

    result = _analyzer(forest, X).analyze(patient)
    assert result is not None
    assert {impact.feature for impact in result.impacts} == set(missing)
    spreads = [impact.spread for impact in result.impacts]
    assert spreads == sorted(spreads, reverse=True)
