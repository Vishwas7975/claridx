import pytest

from app.services.heart_prediction import sensitivity_warning
from ml.sensitivity import FeatureImpact, SensitivityResult
from tests.api.payloads import FULL_PATIENT

URL = "/api/v1/heart/predictions"


def _result(uncertain: bool) -> SensitivityResult:
    return SensitivityResult(
        baseline_probability=0.6,
        probability_min=0.1,
        probability_max=0.99,
        typical_low=0.3,
        typical_high=0.9,
        positive_share=0.55,
        verdict_uncertain=uncertain,
        patterns_used=240,
        impacts=(
            FeatureImpact("thal", 0.1, 0.99, 0.2, 0.95, True),
            FeatureImpact("ca", 0.5, 0.7, 0.55, 0.65, False),
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
    assert sensitivity["probability_min"] <= sensitivity["typical_low"]
    assert sensitivity["typical_low"] <= sensitivity["typical_high"]
    assert sensitivity["typical_high"] <= sensitivity["probability_max"]
    assert sensitivity["probability_min"] <= sensitivity["baseline_probability"]
    assert sensitivity["baseline_probability"] <= sensitivity["probability_max"]
    assert sensitivity["baseline_probability"] == pytest.approx(body["probability"])
    assert 0.0 <= sensitivity["positive_share"] <= 1.0
    assert sensitivity["patterns_used"] > 0
    assert "assumptions" in sensitivity["note"]


def test_warning_when_verdict_is_uncertain() -> None:
    warning = sensitivity_warning(_result(uncertain=True))
    assert warning is not None
    assert "55%" in warning
    assert "Thallium stress test result" in warning
    assert "0.20" in warning
    assert "0.95" in warning


def test_no_warning_when_verdict_is_stable() -> None:
    assert sensitivity_warning(_result(uncertain=False)) is None
