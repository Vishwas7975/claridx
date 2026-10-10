import numpy as np
import pytest

from ml.explain import ShapExplainer
from ml.pipelines.heart import FEATURES, build_models
from tests.pipelines.synthetic import make_heart_like_data


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


def test_forest_explanation_is_additive_in_probability(forest, data) -> None:
    X, _ = data
    result = ShapExplainer(forest, X).explain(X.iloc[[5]])
    total = result.base_value + sum(item.contribution for item in result.contributions)
    assert result.output_space == "probability"
    assert total == pytest.approx(result.probability, abs=1e-6)


def test_logistic_explanation_is_additive_in_log_odds(logistic, data) -> None:
    X, _ = data
    result = ShapExplainer(logistic, X).explain(X.iloc[[9]])
    total = result.base_value + sum(item.contribution for item in result.contributions)
    log_odds = np.log(result.probability / (1 - result.probability))
    assert result.output_space == "log_odds"
    assert total == pytest.approx(log_odds, abs=1e-6)


def test_logistic_shap_matches_closed_form(logistic, data) -> None:
    """For a linear model SHAP must equal coefficient * (x - mean of background)."""
    X, _ = data
    preprocess = logistic.named_steps["preprocess"]
    coefficients = logistic.named_steps["model"].coef_[0]
    patient = X.iloc[[7]]

    expected = coefficients * (
        preprocess.transform(patient)[0] - preprocess.transform(X).mean(axis=0)
    )
    actual = np.array(list(ShapExplainer(logistic, X).column_contributions(patient).values()))
    np.testing.assert_allclose(actual, expected, atol=1e-8)


def test_aggregation_preserves_total_and_covers_every_feature(forest, data) -> None:
    X, _ = data
    explainer = ShapExplainer(forest, X)
    patient = X.iloc[[3]]
    per_column = explainer.column_contributions(patient)
    result = explainer.explain(patient)
    aggregated = sum(item.contribution for item in result.contributions)
    assert sum(per_column.values()) == pytest.approx(aggregated, abs=1e-9)
    assert {item.feature for item in result.contributions} == set(FEATURES)


def test_missing_input_is_flagged_and_explanation_stays_additive(forest, data) -> None:
    X, _ = data
    patient = X.iloc[[2]].copy()
    patient["chol"] = np.nan
    result = ShapExplainer(forest, X).explain(patient)
    chol = next(item for item in result.contributions if item.feature == "chol")
    total = result.base_value + sum(item.contribution for item in result.contributions)
    assert chol.imputed is True
    assert chol.value is None
    assert total == pytest.approx(result.probability, abs=1e-6)


def test_unsupported_model_is_rejected(data) -> None:
    X, y = data
    model = build_models(0)["gradient_boosting"].fit(X, y)
    with pytest.raises(NotImplementedError):
        ShapExplainer(model, X)
