import numpy as np
import pytest

from ml.explain import LimeExplainer, ShapExplainer, compare
from ml.pipelines.diabetes import (
    FEATURES as DIABETES_FEATURES,
)
from ml.pipelines.diabetes import (
    SUSPICIOUS_ZERO_FEATURES,
    build_models,
)
from tests.pipelines.synthetic import make_diabetes_like_data


@pytest.fixture(scope="module")
def synthetic_data():
    X, y = make_diabetes_like_data(rows=120, seed=42)
    return X, y


@pytest.fixture(scope="module")
def background(synthetic_data):
    X, _ = synthetic_data
    return X.copy()


@pytest.fixture(scope="module")
def forest(synthetic_data):
    X, y = synthetic_data
    return build_models(0)["random_forest"].fit(X, y)


@pytest.fixture(scope="module")
def logistic(synthetic_data):
    X, y = synthetic_data
    return build_models(0)["logistic_regression"].fit(X, y)


def test_diabetes_forest_shap_is_additive_in_probability(forest, background) -> None:
    explainer = ShapExplainer(
        forest,
        background,
        features=DIABETES_FEATURES,
        zero_as_missing=SUSPICIOUS_ZERO_FEATURES,
    )
    patient = background.iloc[[3]]
    result = explainer.explain(patient)

    total = result.base_value + sum(item.contribution for item in result.contributions)
    assert result.output_space == "probability"
    assert abs(total - result.probability) < 1e-6
    expected_prob = float(forest.predict_proba(patient)[0, 1])
    assert result.probability == pytest.approx(expected_prob, abs=1e-6)


def test_diabetes_logistic_shap_is_additive_in_log_odds(logistic, background) -> None:
    explainer = ShapExplainer(
        logistic,
        background,
        features=DIABETES_FEATURES,
        zero_as_missing=SUSPICIOUS_ZERO_FEATURES,
    )
    patient = background.iloc[[5]]
    result = explainer.explain(patient)

    total = result.base_value + sum(item.contribution for item in result.contributions)
    assert result.output_space == "log_odds"
    log_odds = np.log(result.probability / (1.0 - result.probability))
    assert abs(total - log_odds) < 1e-5


def test_diabetes_shap_covers_all_eight_features(forest, background) -> None:
    explainer = ShapExplainer(
        forest,
        background,
        features=DIABETES_FEATURES,
        zero_as_missing=SUSPICIOUS_ZERO_FEATURES,
    )
    result = explainer.explain(background.iloc[[0]])
    assert {item.feature for item in result.contributions} == set(DIABETES_FEATURES)
    assert len(result.contributions) == 8


def test_diabetes_shap_missing_and_zero_imputation_flags(forest, background) -> None:
    explainer = ShapExplainer(
        forest,
        background,
        features=DIABETES_FEATURES,
        zero_as_missing=SUSPICIOUS_ZERO_FEATURES,
    )
    patient = background.iloc[[1]].copy()
    patient["plas"] = np.nan  # explicit NaN
    patient["insu"] = 0.0  # suspicious zero: imputed by pipeline
    patient["preg"] = 0.0  # valid physiological zero: not imputed

    result = explainer.explain(patient)

    plas = next(item for item in result.contributions if item.feature == "plas")
    insu = next(item for item in result.contributions if item.feature == "insu")
    preg = next(item for item in result.contributions if item.feature == "preg")

    assert plas.imputed is True
    assert plas.value is None

    assert insu.imputed is True
    assert insu.value == 0.0

    assert preg.imputed is False
    assert preg.value == 0.0

    # Additivity remains satisfied with imputed inputs:
    total = result.base_value + sum(item.contribution for item in result.contributions)
    assert abs(total - result.probability) < 1e-6


def test_diabetes_lime_explainer_covers_all_features_and_probability_bounds(
    forest, background
) -> None:
    explainer = LimeExplainer(
        forest,
        background,
        num_samples=300,
        features=DIABETES_FEATURES,
        zero_as_missing=SUSPICIOUS_ZERO_FEATURES,
        class_names=["tested_negative", "tested_positive"],
    )
    result = explainer.explain(background.iloc[[2]])

    assert {item.feature for item in result.contributions} == set(DIABETES_FEATURES)
    assert result.output_space == "probability"
    assert 0.0 <= result.probability <= 1.0
    assert result.fidelity is not None


def test_diabetes_lime_is_reproducible_under_fixed_seed(forest, background) -> None:
    explainer = LimeExplainer(
        forest,
        background,
        num_samples=300,
        seed=42,
        features=DIABETES_FEATURES,
        zero_as_missing=SUSPICIOUS_ZERO_FEATURES,
    )
    patient = background.iloc[[4]]
    first = explainer.explain(patient)
    second = explainer.explain(patient)
    assert first.contributions == second.contributions


def test_diabetes_lime_imputation_flags(forest, background) -> None:
    explainer = LimeExplainer(
        forest,
        background,
        num_samples=300,
        features=DIABETES_FEATURES,
        zero_as_missing=SUSPICIOUS_ZERO_FEATURES,
    )
    patient = background.iloc[[0]].copy()
    patient["mass"] = np.nan
    patient["skin"] = 0.0
    patient["preg"] = 0.0

    result = explainer.explain(patient)

    mass = next(item for item in result.contributions if item.feature == "mass")
    skin = next(item for item in result.contributions if item.feature == "skin")
    preg = next(item for item in result.contributions if item.feature == "preg")

    assert mass.imputed is True
    assert mass.value is None

    assert skin.imputed is True
    assert skin.value == 0.0

    assert preg.imputed is False
    assert preg.value == 0.0


def test_diabetes_shap_and_lime_agreement(forest, background) -> None:
    shap_exp = ShapExplainer(
        forest,
        background,
        features=DIABETES_FEATURES,
        zero_as_missing=SUSPICIOUS_ZERO_FEATURES,
    )
    lime_exp = LimeExplainer(
        forest,
        background,
        num_samples=300,
        features=DIABETES_FEATURES,
        zero_as_missing=SUSPICIOUS_ZERO_FEATURES,
    )
    patient = background.iloc[[6]]
    s_res = shap_exp.explain(patient)
    l_res = lime_exp.explain(patient)

    agreement = compare(s_res, l_res, k=3)
    assert agreement.k == 3
    assert 0.0 <= agreement.top_k_overlap <= 1.0
    assert 0.0 <= agreement.sign_agreement <= 1.0


def test_explainer_fails_on_missing_background_features(forest, background) -> None:
    bad_background = background.drop(columns=["age"])
    with pytest.raises(ValueError, match="Background missing features.*age"):
        ShapExplainer(
            forest,
            bad_background,
            features=DIABETES_FEATURES,
        )

    with pytest.raises(ValueError, match="Background missing features.*age"):
        LimeExplainer(
            forest,
            bad_background,
            features=DIABETES_FEATURES,
        )


def test_unsupported_model_rejected(synthetic_data, background) -> None:
    X, y = synthetic_data
    gb = build_models(0)["gradient_boosting"].fit(X, y)
    with pytest.raises(NotImplementedError, match="SHAP explanations are not implemented"):
        ShapExplainer(gb, background, features=DIABETES_FEATURES)
