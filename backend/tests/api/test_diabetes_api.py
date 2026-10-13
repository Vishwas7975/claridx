import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_diabetes_registry
from app.domain.diabetes_features import FEATURE_SPECS, LABELS
from app.main import app
from app.services.diabetes_registry import DiabetesModelRegistry
from ml.pipelines.diabetes import FEATURES, build_models
from tests.pipelines.synthetic import make_diabetes_like_data

URL = "/api/v1/diabetes/predictions"

FULL_DIABETES_PATIENT = {
    "preg": 2,
    "plas": 120.0,
    "pres": 70.0,
    "skin": 25.0,
    "insu": 100.0,
    "mass": 28.5,
    "pedi": 0.35,
    "age": 35,
}


@pytest.fixture(scope="session")
def diabetes_registry() -> DiabetesModelRegistry:
    X, y = make_diabetes_like_data()
    candidates = build_models(0)
    pipelines = {
        name: candidates[name].fit(X, y) for name in ("logistic_regression", "random_forest")
    }
    return DiabetesModelRegistry.from_models(
        pipelines, X, version="test-diabetes-1", lime_samples=100
    )


@pytest.fixture
def client(diabetes_registry: DiabetesModelRegistry):
    app.dependency_overrides[get_diabetes_registry] = lambda: diabetes_registry
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def client_without_models():
    app.dependency_overrides.clear()
    app.state.diabetes_registry = None
    return TestClient(app)


def test_diabetes_prediction_returns_full_explanation_and_omits_agreement(client) -> None:
    response = client.post(URL, json={"patient": FULL_DIABETES_PATIENT})
    assert response.status_code == 200
    body = response.json()

    assert body["model_name"] == "logistic_regression"
    assert body["model_version"] == "test-diabetes-1"
    assert 0.0 <= body["probability"] <= 1.0
    assert body["threshold"] == 0.5
    assert body["calibrated"] is False
    assert body["imputed_features"] == []
    assert "Decision support and educational prototype only" in body["disclaimer"]
    assert body["shap"]["output_space"] == "log_odds"
    assert body["lime"]["output_space"] == "probability"
    assert body["agreement"] is None
    assert any("Cross-explainer agreement metrics are omitted" in w for w in body["warnings"])

    for method in ("shap", "lime"):
        assert {c["feature"] for c in body[method]["contributions"]} == set(FEATURES)


def test_diabetes_random_forest_can_be_selected_and_includes_agreement(client) -> None:
    payload = {"model_name": "random_forest", "patient": FULL_DIABETES_PATIENT}
    response = client.post(URL, json=payload)
    assert response.status_code == 200
    body = response.json()

    assert body["model_name"] == "random_forest"
    assert body["shap"]["output_space"] == "probability"
    assert body["lime"]["output_space"] == "probability"
    assert body["agreement"] is not None
    assert body["agreement"]["k"] == 3
    assert 0.0 <= body["agreement"]["top_k_overlap"] <= 1.0
    assert 0.0 <= body["agreement"]["sign_agreement"] <= 1.0


def test_missing_inputs_are_reported_and_flagged(client) -> None:
    patient = {k: v for k, v in FULL_DIABETES_PATIENT.items() if k not in ("insu", "skin")}
    body = client.post(URL, json={"patient": patient}).json()

    assert set(body["imputed_features"]) == {"skin", "insu"}
    for method in ("shap", "lime"):
        flagged = {c["feature"] for c in body[method]["contributions"]}
        assert flagged == set(FEATURES)
        flagged_imputed = {c["feature"] for c in body[method]["contributions"] if c["imputed"]}
        assert flagged_imputed == {"skin", "insu"}


def test_suspicious_zeros_are_treated_as_unmeasured_and_flagged(client) -> None:
    patient = {**FULL_DIABETES_PATIENT, "insu": 0.0, "skin": 0.0}
    body = client.post(URL, json={"patient": patient}).json()

    assert set(body["imputed_features"]) == {"skin", "insu"}
    for method in ("shap", "lime"):
        flagged = {c["feature"] for c in body[method]["contributions"] if c["imputed"]}
        assert flagged == {"skin", "insu"}
    assert any("was entered as 0, which represents unmeasured data" in w for w in body["warnings"])


def test_preg_zero_is_valid_and_not_imputed(client) -> None:
    patient = {**FULL_DIABETES_PATIENT, "preg": 0}
    body = client.post(URL, json={"patient": patient}).json()

    assert "preg" not in body["imputed_features"]
    for method in ("shap", "lime"):
        preg_item = next(c for c in body[method]["contributions"] if c["feature"] == "preg")
        assert preg_item["imputed"] is False
        assert preg_item["value"] == 0.0


def test_effective_measurements_safeguard_rejects_few_measurements(client) -> None:
    patient = {"age": 30, "preg": 1, "pedi": 0.5, "plas": 110.0}
    response = client.post(URL, json={"patient": patient})
    assert response.status_code == 422


def test_effective_measurements_safeguard_excludes_suspicious_zeros(client) -> None:
    patient = {
        "age": 30,
        "preg": 1,
        "pedi": 0.5,
        "plas": 0.0,
        "insu": 0.0,
    }
    response = client.post(URL, json={"patient": patient})
    assert response.status_code == 422


def test_unknown_field_is_rejected(client) -> None:
    patient = {**FULL_DIABETES_PATIENT, "unknown_field": 123}
    assert client.post(URL, json={"patient": patient}).status_code == 422


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("age", 18),
        ("age", 130),
        ("plas", -5.0),
        ("pres", -1.0),
        ("mass", 110.0),
        ("pedi", -0.1),
    ],
)
def test_invalid_bounds_are_rejected(client, field: str, value: float) -> None:
    patient = {**FULL_DIABETES_PATIENT, field: value}
    assert client.post(URL, json={"patient": patient}).status_code == 422


def test_empirical_range_warnings_issued_for_out_of_training_distribution(client) -> None:
    patient = {**FULL_DIABETES_PATIENT, "pedi": 2.8}
    body = client.post(URL, json={"patient": patient}).json()
    expected_msg = f"{LABELS['pedi']} = 2.8 is outside the range seen in training data"
    assert any(expected_msg in w for w in body["warnings"])


def test_validation_errors_are_sanitized(client) -> None:
    patient = {**FULL_DIABETES_PATIENT, "age": 12}
    response = client.post(URL, json={"patient": patient})
    assert response.status_code == 422
    assert "12" not in response.text


def test_prediction_unavailable_without_models_returns_503(client_without_models) -> None:
    response = client_without_models.post(URL, json={"patient": FULL_DIABETES_PATIENT})
    assert response.status_code == 503


def test_malformed_metrics_json_raises_value_error(tmp_path: Path) -> None:
    (tmp_path / "metrics.json").write_text(json.dumps({"invalid": "structure"}))
    (tmp_path / "background.csv").write_text("dummy")
    for name in ("logistic_regression", "random_forest"):
        (tmp_path / f"{name}.joblib").write_text("dummy")

    with pytest.raises(ValueError, match="Malformed metrics.json"):
        DiabetesModelRegistry.load(tmp_path)


def test_features_endpoint_lists_every_diabetes_feature(client) -> None:
    response = client.get("/api/v1/diabetes/features")
    assert response.status_code == 200
    features = response.json()
    assert len(features) == len(FEATURE_SPECS)
    assert [f["name"] for f in features] == [spec.name for spec in FEATURE_SPECS]


def test_models_endpoint_lists_both_models_with_correct_roles(client) -> None:
    body = client.get("/api/v1/diabetes/models").json()
    assert body["model_version"] == "test-diabetes-1"
    assert body["primary"] == "logistic_regression"
    assert {model["name"] for model in body["models"]} == {
        "logistic_regression",
        "random_forest",
    }
