import numpy as np
import pytest

from ml.explain import LimeExplainer
from ml.pipelines.heart import FEATURES, build_models
from tests.pipelines.synthetic import make_heart_like_data


@pytest.fixture(scope="module")
def data():
    return make_heart_like_data()


@pytest.fixture(scope="module")
def explainer(data):
    X, y = data
    forest = build_models(0)["random_forest"].fit(X, y)
    return LimeExplainer(forest, X, num_samples=500)


def test_lime_covers_every_feature(explainer, data) -> None:
    X, _ = data
    result = explainer.explain(X.iloc[[0]])
    assert {item.feature for item in result.contributions} == set(FEATURES)
    assert result.output_space == "probability"
    assert 0.0 <= result.probability <= 1.0


def test_lime_is_reproducible(explainer, data) -> None:
    X, _ = data
    first = explainer.explain(X.iloc[[1]])
    second = explainer.explain(X.iloc[[1]])
    assert first.contributions == second.contributions


def test_lime_flags_imputed_inputs(explainer, data) -> None:
    X, _ = data
    patient = X.iloc[[0]].copy()
    patient["ca"] = np.nan
    result = explainer.explain(patient)
    ca = next(item for item in result.contributions if item.feature == "ca")
    assert ca.imputed is True
    assert ca.value is None
