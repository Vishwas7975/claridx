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


class ThalCaStub:
    """Predicts disease only when thal is 7 and ca is 3 together."""

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        positive = np.where((X["thal"] == 7) & (X["ca"] == 3), 0.9, 0.1)
        return np.column_stack([1 - positive, positive])


@pytest.fixture(scope="module")
def data():
    return make_heart_like_data()


@pytest.fixture(scope="module")
def forest(data):
    X, y = data
    return build_models(0)["random_forest"].fit(X, y)


@pytest.fixture(scope="module")
def logistic(data):
    X, y = data
    return build_models(0)["logistic_regression"].fit(X, y)


def _probability(model, patient: pd.DataFrame, **values: float) -> float:
    row = patient.copy()
    for name, value in values.items():
        row[name] = value
    return float(model.predict_proba(row)[0, 1])


def test_no_missing_values_means_no_sensitivity(forest, data) -> None:
    X, _ = data
    assert SensitivityAnalyzer(forest, X).analyze(X.iloc[[0]]) is None


def test_uncertain_when_decisive_feature_is_missing(data) -> None:
    X, _ = data
    patient = X.iloc[[0]].copy()
    patient["thal"] = np.nan
    result = SensitivityAnalyzer(ThalStub(), X).analyze(patient)

    expected_share = float((X["thal"] == 7).mean())
    assert 0.1 <= expected_share <= 0.9  # the synthetic data must make this a real test
    assert result is not None
    assert result.positive_share == pytest.approx(expected_share)
    assert result.verdict_uncertain is True
    assert result.baseline_probability == pytest.approx(0.1)
    assert result.typical_high == pytest.approx(0.9)
    assert result.impacts[0].feature == "thal"
    assert result.impacts[0].can_flip is True


def test_stable_when_missing_feature_does_not_matter(data) -> None:
    X, _ = data
    patient = X.iloc[[0]].copy()
    patient["thal"] = 3.0
    patient["chol"] = np.nan
    result = SensitivityAnalyzer(ThalStub(), X).analyze(patient)

    assert result is not None
    assert result.positive_share == pytest.approx(0.0)
    assert result.verdict_uncertain is False
    assert result.impacts[0].spread == pytest.approx(0.0)
    assert result.impacts[0].can_flip is False


def test_rare_extreme_is_not_mistaken_for_typical(data) -> None:
    """A value seen in only 5% of patients sets the extreme but must not drive the verdict."""
    X, _ = data
    background = X.copy()
    background["thal"] = 3.0
    background.iloc[:8, background.columns.get_loc("thal")] = 7.0  # 8 of 160 patients
    patient = X.iloc[[0]].copy()
    patient["thal"] = np.nan

    result = SensitivityAnalyzer(ThalStub(), background).analyze(patient)
    assert result is not None
    assert result.probability_max == pytest.approx(0.9)
    assert result.typical_high == pytest.approx(0.1)
    assert result.positive_share == pytest.approx(0.05)
    assert result.verdict_uncertain is False


def test_joint_scenarios_keep_values_of_the_same_patient_together(data) -> None:
    X, _ = data
    background = X.copy()
    half = len(background) // 2
    background["thal"] = 3.0
    background["ca"] = 0.0
    background.iloc[:half, background.columns.get_loc("thal")] = 7.0
    background.iloc[:half, background.columns.get_loc("ca")] = 3.0
    patient = X.iloc[[0]].copy()
    patient["thal"] = np.nan
    patient["ca"] = np.nan

    result = SensitivityAnalyzer(ThalCaStub(), background).analyze(patient)
    assert result is not None
    # Every positive scenario needs thal=7 and ca=3 together, which only half the patients have.
    assert result.positive_share == pytest.approx(0.5)
    assert result.probability_max == pytest.approx(0.9)


def test_matches_independent_per_patient_computation(logistic, data) -> None:
    X, _ = data
    patient = X.iloc[[3]].copy()
    patient["thal"] = np.nan
    patient["ca"] = np.nan

    expected = np.array(
        [_probability(logistic, patient, thal=row["thal"], ca=row["ca"]) for _, row in X.iterrows()]
    )
    result = SensitivityAnalyzer(logistic, X).analyze(patient)

    assert result is not None
    assert result.patterns_used == len(X)
    assert result.positive_share == pytest.approx(float(np.mean(expected >= 0.5)))
    assert result.typical_low == pytest.approx(float(np.percentile(expected, 10)))
    assert result.typical_high == pytest.approx(float(np.percentile(expected, 90)))


@pytest.mark.parametrize("name", ["random_forest", "logistic_regression"])
def test_ranges_are_nested_and_contain_the_baseline(name: str, data) -> None:
    X, y = data
    model = build_models(0)[name].fit(X, y)
    patient = X.iloc[[5]].copy()
    patient["chol"] = np.nan
    patient["ca"] = np.nan
    result = SensitivityAnalyzer(model, X).analyze(patient)

    assert result is not None
    assert result.probability_min <= result.typical_low <= result.typical_high
    assert result.typical_high <= result.probability_max
    assert result.probability_min <= result.baseline_probability <= result.probability_max
    assert 0.0 <= result.positive_share <= 1.0


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


def test_no_sensitivity_when_no_training_patient_has_the_missing_values(forest, data) -> None:
    X, _ = data
    background = X.copy()
    background["thal"] = np.nan
    patient = X.iloc[[0]].copy()
    patient["thal"] = np.nan
    assert SensitivityAnalyzer(forest, background).analyze(patient) is None
