import pytest

from app.services.heart_prediction import sensitivity_warning
from ml.sensitivity import FeatureImpact, SensitivityResult
from tests.api.payloads import FULL_PATIENT

URL = "/api/v1/heart/predictions"


def _result(can_flip: bool) -> SensitivityResult:
    return SensitivityResult(
        baseline_probability=0.6,
        probability_min=0.2,
        probability_max=0.99,
        can_flip=can_flip,
        exhaustive=True,
        scenarios_evaluated=10,
        impacts=(
            FeatureImpact("thal", 0.2, 0.99, can_flip),
            FeatureImpact("ca", 0.5, 0.7, False),
        ),
    )


def test_full_patient_has_no_sensitivity_block(client) -> None:
    body = client.post(URL, json={"patient": FULL_PATIENT}).json()
    assert body["sensitivity"] is None


def test_missing_inputs_include_sensitivity(client) -> None:
    patient = {k: v for k, v in FULL_PATIENT.items() if k not in ("chol", "ca")}
    body = client.post(URL, json={"patient": patient}).json()
    sensitivity = body["sensitivity"]

    assert sensitivity is not None
    assert {impact["feature"] for impact in sensitivity["impacts"]} == {"chol", "ca"}
    assert sensitivity["probability_min"] <= sensitivity["baseline_probability"]
    assert sensitivity["baseline_probability"] <= sensitivity["probability_max"]
    assert sensitivity["baseline_probability"] == pytest.approx(body["probability"])
    assert sensitivity["scenarios_evaluated"] > 0
    assert "assumptions" in sensitivity["note"]


def test_flip_warning_names_most_influential_feature() -> None:
    warning = sensitivity_warning(_result(can_flip=True))
    assert warning is not None
    assert "Thallium stress test result" in warning
    assert "0.20" in warning
    assert "0.99" in warning


def test_no_warning_when_verdict_is_stable() -> None:
    assert sensitivity_warning(_result(can_flip=False)) is None
