"""Startup behaviour: stay up without model artifacts, and load real ones when present."""

from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

import app.main as main_module
from app.core.config import get_settings
from app.main import app
from tests.api.payloads import FULL_PATIENT

URL = "/api/v1/heart/predictions"
REAL_ARTIFACTS = get_settings().model_artifacts_dir / "heart"


def test_api_starts_without_artifacts_and_reports_models_unavailable(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(
        main_module, "get_settings", lambda: SimpleNamespace(model_artifacts_dir=tmp_path)
    )
    with TestClient(app) as client:
        assert client.get("/api/v1/health").status_code == 200
        assert client.get("/api/v1/heart/features").status_code == 200
        assert client.get("/api/v1/heart/models").status_code == 503
        assert client.post(URL, json={"patient": FULL_PATIENT}).status_code == 503


@pytest.mark.skipif(
    not (REAL_ARTIFACTS / "metrics.json").exists(), reason="trained artifacts not present"
)
def test_real_artifacts_load_and_serve_predictions() -> None:
    with TestClient(app) as client:
        models = client.get("/api/v1/heart/models")
        assert models.status_code == 200
        assert models.json()["model_version"].startswith("heart-")

        full = client.post(URL, json={"patient": FULL_PATIENT}).json()
        assert 0.0 <= full["probability"] <= 1.0
        assert full["sensitivity"] is None

        partial_patient = {k: v for k, v in FULL_PATIENT.items() if k not in ("chol", "ca", "thal")}
        partial = client.post(URL, json={"patient": partial_patient}).json()
        assert partial["imputed_features"] == ["chol", "ca", "thal"]
        assert partial["sensitivity"] is not None
