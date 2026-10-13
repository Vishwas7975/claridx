import pytest

from ml.pipelines.heart import FEATURES
from tests.api.payloads import FULL_PATIENT

URL = "/api/v1/heart/predictions"


def test_prediction_returns_full_explanation(client) -> None:
    response = client.post(URL, json={"patient": FULL_PATIENT})
    assert response.status_code == 200
    body = response.json()

    assert body["model_name"] == "random_forest"
    assert body["model_version"] == "test-1"
    assert 0.0 <= body["probability"] <= 1.0
    assert body["calibrated"] is False
    assert body["imputed_features"] == []
    assert body["disclaimer"]
    for method in ("shap", "lime"):
        assert {c["feature"] for c in body[method]["contributions"]} == set(FEATURES)
    assert body["shap"]["output_space"] == "probability"
    assert body["shap"]["base_value"] is not None
    assert body["lime"]["fidelity"] is not None
    assert body["agreement"]["k"] == 3


def test_missing_inputs_are_reported_and_flagged(client) -> None:
    patient = {k: v for k, v in FULL_PATIENT.items() if k not in ("chol", "ca")}
    body = client.post(URL, json={"patient": patient}).json()

    assert body["imputed_features"] == ["chol", "ca"]
    for method in ("shap", "lime"):
        flagged = {c["feature"] for c in body[method]["contributions"] if c["imputed"]}
        assert flagged == {"chol", "ca"}


def test_too_few_measurements_are_rejected(client) -> None:
    response = client.post(URL, json={"patient": {"age": 54, "sex": 1}})
    assert response.status_code == 422


def test_unknown_field_is_rejected(client) -> None:
    patient = {**FULL_PATIENT, "chlo": 240}
    assert client.post(URL, json={"patient": patient}).status_code == 422


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("age", 5),
        ("age", 200),
        ("trestbps", 400),
        ("oldpeak", -1),
        ("cp", 9),
        ("sex", 2),
    ],
)
def test_invalid_values_are_rejected(client, field: str, value: int) -> None:
    patient = {**FULL_PATIENT, field: value}
    assert client.post(URL, json={"patient": patient}).status_code == 422


def test_value_outside_training_range_warns(client) -> None:
    patient = {**FULL_PATIENT, "chol": 600}
    body = client.post(URL, json={"patient": patient}).json()
    assert any("outside the range seen in training data" in w for w in body["warnings"])


def test_logistic_regression_can_be_selected(client) -> None:
    payload = {"model_name": "logistic_regression", "patient": FULL_PATIENT}
    body = client.post(URL, json=payload).json()
    assert body["model_name"] == "logistic_regression"
    assert body["shap"]["output_space"] == "log_odds"
    assert body["lime"]["output_space"] == "probability"


def test_unknown_model_is_rejected(client) -> None:
    payload = {"model_name": "gradient_boosting", "patient": FULL_PATIENT}
    assert client.post(URL, json=payload).status_code == 422


def test_prediction_unavailable_without_models(client_without_models) -> None:
    response = client_without_models.post(URL, json={"patient": FULL_PATIENT})
    assert response.status_code == 503


def test_features_endpoint_lists_every_feature(client) -> None:
    response = client.get("/api/v1/heart/features")
    assert response.status_code == 200
    assert {spec["name"] for spec in response.json()} == set(FEATURES)


def test_models_endpoint_lists_both_models(client) -> None:
    body = client.get("/api/v1/heart/models").json()
    assert body["model_version"] == "test-1"
    assert body["primary"] == "random_forest"
    assert {model["name"] for model in body["models"]} == {"random_forest", "logistic_regression"}


def test_heart_prediction_response_shape_unchanged(client) -> None:
    response = client.post(URL, json={"patient": FULL_PATIENT})
    assert response.status_code == 200
    body = response.json()
    expected_agreement_keys = {"rank_correlation", "top_k_overlap", "sign_agreement", "k"}
    assert set(body["agreement"].keys()) == expected_agreement_keys
    expected_top_level_keys = {
        "model_name",
        "model_version",
        "probability",
        "threshold",
        "predicted_positive",
        "calibrated",
        "imputed_features",
        "warnings",
        "shap",
        "lime",
        "agreement",
        "sensitivity",
        "disclaimer",
    }
    assert set(body.keys()) == expected_top_level_keys
