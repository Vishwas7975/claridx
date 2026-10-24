import pandas as pd
import pytest

from app.services.model_registry import ModelRegistry
from ml.pipelines.heart import FEATURES, NUMERIC_FEATURES, ORDINAL_FEATURES


class MockConstantModel:
    def __init__(self, proba: float):
        self._proba = proba

    def predict_proba(self, X: pd.DataFrame):
        return [[1.0 - self._proba, self._proba]]


class MockFailingModel:
    def predict_proba(self, X: pd.DataFrame):
        raise ValueError("Simulated model failure (e.g. matrix singularity)")


def _make_dummy_registry(pipelines: dict[str, any]) -> ModelRegistry:
    # Minimal background
    # bg
    pd.DataFrame([{f: 50.0 for f in FEATURES}])
    ranges = {f: (0.0, 100.0) for f in NUMERIC_FEATURES + ORDINAL_FEATURES}
    return ModelRegistry(
        version="test-consensus-1",
        models={},
        training_ranges=ranges,
        candidate_pipelines=pipelines,
    )


def test_majority_voting_all_positive():
    frame = pd.DataFrame([{f: 50.0 for f in FEATURES}])
    pipes = {
        "random_forest": MockConstantModel(0.8),
        "logistic_regression": MockConstantModel(0.7),
        "gradient_boosting": MockConstantModel(0.9),
        "mlp": MockConstantModel(0.6),
    }
    registry = _make_dummy_registry(pipes)
    is_pos, v_pos, v_neg, results, summary = registry.predict_all(frame, threshold=0.5)

    assert is_pos is True
    assert v_pos == 4
    assert v_neg == 0
    assert len(results) == 4
    assert all(r["status"] == "success" for r in results)


def test_majority_voting_three_negative_one_positive():
    frame = pd.DataFrame([{f: 50.0 for f in FEATURES}])
    pipes = {
        "random_forest": MockConstantModel(0.2),
        "logistic_regression": MockConstantModel(0.3),
        "gradient_boosting": MockConstantModel(0.8),  # one outlier positive
        "mlp": MockConstantModel(0.1),
    }
    registry = _make_dummy_registry(pipes)
    is_pos, v_pos, v_neg, results, summary = registry.predict_all(frame, threshold=0.5)

    assert is_pos is False
    assert v_pos == 1
    assert v_neg == 3


def test_majority_voting_tie_broken_by_primary_model():
    frame = pd.DataFrame([{f: 50.0 for f in FEATURES}])
    # 2 positive, 2 negative. Primary model (random_forest) is positive (0.6).
    pipes_rf_pos = {
        "random_forest": MockConstantModel(0.6),  # primary -> positive
        "logistic_regression": MockConstantModel(0.2),
        "gradient_boosting": MockConstantModel(0.7),
        "mlp": MockConstantModel(0.4),
    }
    reg1 = _make_dummy_registry(pipes_rf_pos)
    is_pos1, v_pos1, v_neg1, _, _ = reg1.predict_all(frame, threshold=0.5)
    assert is_pos1 is True
    assert v_pos1 == 2
    assert v_neg1 == 2

    # Now primary model is negative (0.4)
    pipes_rf_neg = {
        "random_forest": MockConstantModel(0.4),  # primary -> negative
        "logistic_regression": MockConstantModel(0.8),
        "gradient_boosting": MockConstantModel(0.3),
        "mlp": MockConstantModel(0.9),
    }
    reg2 = _make_dummy_registry(pipes_rf_neg)
    is_pos2, v_pos2, v_neg2, _, _ = reg2.predict_all(frame, threshold=0.5)
    assert is_pos2 is False
    assert v_pos2 == 2
    assert v_neg2 == 2


def test_model_failure_handled_gracefully_not_silently_negative():
    frame = pd.DataFrame([{f: 50.0 for f in FEATURES}])
    # MLP fails, but other 3 succeed (2 positive, 1 negative)
    pipes = {
        "random_forest": MockConstantModel(0.7),
        "logistic_regression": MockConstantModel(0.3),
        "gradient_boosting": MockConstantModel(0.8),
        "mlp": MockFailingModel(),
    }
    registry = _make_dummy_registry(pipes)
    is_pos, v_pos, v_neg, results, summary = registry.predict_all(frame, threshold=0.5)

    assert is_pos is True
    assert v_pos == 2
    assert v_neg == 1

    mlp_res = next(r for r in results if r["model_name"] == "mlp")
    assert mlp_res["status"] == "failed"
    assert "Simulated model failure" in mlp_res["error_message"]
    assert mlp_res["probability"] is None
    assert mlp_res["predicted_positive"] is None


def test_all_models_failing_raises_runtime_error():
    frame = pd.DataFrame([{f: 50.0 for f in FEATURES}])
    pipes = {
        "random_forest": MockFailingModel(),
        "logistic_regression": MockFailingModel(),
        "gradient_boosting": MockFailingModel(),
        "mlp": MockFailingModel(),
    }
    registry = _make_dummy_registry(pipes)
    with pytest.raises(RuntimeError, match="Too few models succeeded"):
        registry.predict_all(frame, threshold=0.5)


def test_too_few_models_succeeding_raises_runtime_error():
    frame = pd.DataFrame([{f: 50.0 for f in FEATURES}])
    # 2 models fail, only 2 succeed -> insufficient for defensible consensus
    pipes = {
        "random_forest": MockConstantModel(0.7),
        "logistic_regression": MockConstantModel(0.3),
        "gradient_boosting": MockFailingModel(),
        "mlp": MockFailingModel(),
    }
    registry = _make_dummy_registry(pipes)
    with pytest.raises(RuntimeError, match="Too few models succeeded"):
        registry.predict_all(frame, threshold=0.5)
