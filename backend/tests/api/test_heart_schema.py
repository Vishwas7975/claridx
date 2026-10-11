"""Guards against drift between the feature specs (what the UI shows) and the validation."""

import pytest
from pydantic import ValidationError

from app.domain.heart_features import FEATURE_SPECS
from app.schemas.heart import PatientInput
from tests.api.payloads import FULL_PATIENT


def _accepts(name: str, value: float) -> bool:
    try:
        PatientInput.model_validate({**FULL_PATIENT, name: value})
    except ValidationError:
        return False
    return True


@pytest.mark.parametrize("spec", FEATURE_SPECS, ids=lambda spec: spec.name)
def test_validation_matches_feature_spec(spec) -> None:
    if spec.kind == "number":
        step = spec.step
        assert step is not None
        assert _accepts(spec.name, spec.minimum)
        assert _accepts(spec.name, spec.maximum)
        assert not _accepts(spec.name, spec.minimum - step)
        assert not _accepts(spec.name, spec.maximum + step)
    else:
        allowed = {option.value for option in spec.options}
        for candidate in range(-1, 10):
            assert _accepts(spec.name, candidate) == (candidate in allowed), (spec.name, candidate)
