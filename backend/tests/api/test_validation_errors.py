import json

import pytest

from tests.api.payloads import FULL_PATIENT

URL = "/api/v1/heart/predictions"
JSON_HEADERS = {"Content-Type": "application/json"}


@pytest.mark.parametrize("bad", [float("nan"), float("inf")], ids=["nan", "infinity"])
def test_non_finite_numbers_are_rejected_with_422(client, bad: float) -> None:
    body = json.dumps({"patient": {**FULL_PATIENT, "oldpeak": bad}})
    response = client.post(URL, content=body, headers=JSON_HEADERS)
    assert response.status_code == 422


def test_validation_errors_contain_only_location_message_and_type(client) -> None:
    response = client.post(URL, json={"patient": {**FULL_PATIENT, "age": 5}})
    assert response.status_code == 422

    errors = response.json()["detail"]
    assert errors
    for error in errors:
        assert set(error) == {"loc", "msg", "type"}
    assert any(error["loc"][-1] == "age" for error in errors)
