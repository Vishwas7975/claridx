"""RBAC enforcement tests for heart and diabetes prediction endpoints.

Verifies:
- Unauthenticated requests (no token) -> 401 Unauthorized with WWW-Authenticate: Bearer
- Invalid or expired tokens -> 401 Unauthorized
- Inactive users -> 401 Unauthorized
- Disallowed roles (RESEARCHER) -> 403 Forbidden
- Allowed roles (DOCTOR, ADMIN) -> 200 OK with valid prediction responses
- Public endpoints (health, features, models) remain accessible without authentication
"""

from datetime import timedelta

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_diabetes_registry, get_registry
from app.core.database import SessionLocal
from app.core.security import create_access_token, hash_password
from app.main import app
from app.models.user import User, UserRole
from app.services.diabetes_registry import DiabetesModelRegistry
from app.services.model_registry import ModelRegistry
from ml.pipelines.diabetes import build_models as build_diabetes_models
from ml.pipelines.heart import build_models as build_heart_models
from tests.api.payloads import FULL_PATIENT
from tests.pipelines.synthetic import make_diabetes_like_data, make_heart_like_data

HEART_URL = "/api/v1/heart/predictions"
DIABETES_URL = "/api/v1/diabetes/predictions"

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


@pytest.fixture(scope="module")
def heart_registry() -> ModelRegistry:
    X, y = make_heart_like_data()
    candidates = build_heart_models(0)
    pipelines = {
        name: candidates[name].fit(X, y) for name in ("random_forest", "logistic_regression")
    }
    return ModelRegistry.from_models(pipelines, X, version="test-1", lime_samples=100)


@pytest.fixture(scope="module")
def diabetes_registry() -> DiabetesModelRegistry:
    X, y = make_diabetes_like_data()
    candidates = build_diabetes_models(0)
    pipelines = {
        name: candidates[name].fit(X, y) for name in ("logistic_regression", "random_forest")
    }
    return DiabetesModelRegistry.from_models(
        pipelines, X, version="test-diabetes-1", lime_samples=100
    )


@pytest.fixture(scope="module", autouse=True)
def override_registries(heart_registry: ModelRegistry, diabetes_registry: DiabetesModelRegistry):
    app.dependency_overrides[get_registry] = lambda: heart_registry
    app.dependency_overrides[get_diabetes_registry] = lambda: diabetes_registry
    yield
    app.dependency_overrides.pop(get_registry, None)
    app.dependency_overrides.pop(get_diabetes_registry, None)


def _create_user(email: str, role: UserRole, is_active: bool = True) -> tuple[int, str]:
    with SessionLocal() as db:
        existing = db.query(User).filter_by(email=email).first()
        if existing:
            db.delete(existing)
            db.commit()

        user = User(
            email=email,
            full_name=f"Test {role.value.capitalize()}",
            hashed_password=hash_password("SuperSecret123!"),
            role=role,
            is_active=is_active,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        user_id = user.id
    token = create_access_token(subject=user_id)
    return user_id, token


def _delete_user(user_id: int) -> None:
    with SessionLocal() as db:
        u = db.get(User, user_id)
        if u:
            db.delete(u)
            db.commit()


@pytest.fixture
def doctor_auth():
    user_id, token = _create_user("rbac_doctor@example.com", UserRole.DOCTOR)
    yield {"Authorization": f"Bearer {token}"}
    _delete_user(user_id)


@pytest.fixture
def admin_auth():
    user_id, token = _create_user("rbac_admin@example.com", UserRole.ADMIN)
    yield {"Authorization": f"Bearer {token}"}
    _delete_user(user_id)


@pytest.fixture
def researcher_auth():
    user_id, token = _create_user("rbac_researcher@example.com", UserRole.RESEARCHER)
    yield {"Authorization": f"Bearer {token}"}
    _delete_user(user_id)


@pytest.fixture
def inactive_doctor_auth():
    user_id, token = _create_user("rbac_inactive_doc@example.com", UserRole.DOCTOR, is_active=False)
    yield {"Authorization": f"Bearer {token}"}
    _delete_user(user_id)


@pytest.fixture
def expired_doctor_auth():
    user_id, _ = _create_user("rbac_expired_doc@example.com", UserRole.DOCTOR)
    expired_token = create_access_token(subject=user_id, expires_delta=timedelta(seconds=-10))
    yield {"Authorization": f"Bearer {expired_token}"}
    _delete_user(user_id)


# ---------------------------------------------------------------------------
# Heart Prediction RBAC Tests
# ---------------------------------------------------------------------------


def test_heart_prediction_unauthenticated_returns_401() -> None:
    with TestClient(app) as client:
        res = client.post(HEART_URL, json={"patient": FULL_PATIENT})
        assert res.status_code == 401
        assert res.headers.get("WWW-Authenticate") == "Bearer"
        assert res.json()["detail"] == "Not authenticated"


def test_heart_prediction_invalid_token_returns_401() -> None:
    with TestClient(app) as client:
        res = client.post(
            HEART_URL,
            json={"patient": FULL_PATIENT},
            headers={"Authorization": "Bearer not-a-valid-token"},
        )
        assert res.status_code == 401
        assert res.headers.get("WWW-Authenticate") == "Bearer"


def test_heart_prediction_expired_token_returns_401(expired_doctor_auth) -> None:
    with TestClient(app) as client:
        res = client.post(
            HEART_URL,
            json={"patient": FULL_PATIENT},
            headers=expired_doctor_auth,
        )
        assert res.status_code == 401
        assert res.headers.get("WWW-Authenticate") == "Bearer"


def test_heart_prediction_inactive_user_returns_401(inactive_doctor_auth) -> None:
    with TestClient(app) as client:
        res = client.post(
            HEART_URL,
            json={"patient": FULL_PATIENT},
            headers=inactive_doctor_auth,
        )
        assert res.status_code == 401
        assert res.json()["detail"] == "Inactive user account"


def test_heart_prediction_researcher_returns_403(researcher_auth) -> None:
    with TestClient(app) as client:
        res = client.post(
            HEART_URL,
            json={"patient": FULL_PATIENT},
            headers=researcher_auth,
        )
        assert res.status_code == 403
        assert res.json()["detail"] == "Not enough permissions"


def test_heart_prediction_doctor_authorized(doctor_auth) -> None:
    with TestClient(app) as client:
        res = client.post(
            HEART_URL,
            json={"patient": FULL_PATIENT},
            headers=doctor_auth,
        )
        assert res.status_code == 200
        body = res.json()
        assert 0.0 <= body["probability"] <= 1.0
        assert body["model_name"] == "random_forest"
        assert "shap" in body
        assert "lime" in body


def test_heart_prediction_admin_authorized(admin_auth) -> None:
    with TestClient(app) as client:
        res = client.post(
            HEART_URL,
            json={"patient": FULL_PATIENT},
            headers=admin_auth,
        )
        assert res.status_code == 200
        body = res.json()
        assert 0.0 <= body["probability"] <= 1.0


# ---------------------------------------------------------------------------
# Diabetes Prediction RBAC Tests
# ---------------------------------------------------------------------------


def test_diabetes_prediction_unauthenticated_returns_401() -> None:
    with TestClient(app) as client:
        res = client.post(DIABETES_URL, json={"patient": FULL_DIABETES_PATIENT})
        assert res.status_code == 401
        assert res.headers.get("WWW-Authenticate") == "Bearer"
        assert res.json()["detail"] == "Not authenticated"


def test_diabetes_prediction_invalid_token_returns_401() -> None:
    with TestClient(app) as client:
        res = client.post(
            DIABETES_URL,
            json={"patient": FULL_DIABETES_PATIENT},
            headers={"Authorization": "Bearer malformed.jwt.signature"},
        )
        assert res.status_code == 401
        assert res.headers.get("WWW-Authenticate") == "Bearer"


def test_diabetes_prediction_expired_token_returns_401(expired_doctor_auth) -> None:
    with TestClient(app) as client:
        res = client.post(
            DIABETES_URL,
            json={"patient": FULL_DIABETES_PATIENT},
            headers=expired_doctor_auth,
        )
        assert res.status_code == 401
        assert res.headers.get("WWW-Authenticate") == "Bearer"


def test_diabetes_prediction_inactive_user_returns_401(inactive_doctor_auth) -> None:
    with TestClient(app) as client:
        res = client.post(
            DIABETES_URL,
            json={"patient": FULL_DIABETES_PATIENT},
            headers=inactive_doctor_auth,
        )
        assert res.status_code == 401
        assert res.json()["detail"] == "Inactive user account"


def test_diabetes_prediction_researcher_returns_403(researcher_auth) -> None:
    with TestClient(app) as client:
        res = client.post(
            DIABETES_URL,
            json={"patient": FULL_DIABETES_PATIENT},
            headers=researcher_auth,
        )
        assert res.status_code == 403
        assert res.json()["detail"] == "Not enough permissions"


def test_diabetes_prediction_doctor_authorized(doctor_auth) -> None:
    with TestClient(app) as client:
        res = client.post(
            DIABETES_URL,
            json={"patient": FULL_DIABETES_PATIENT},
            headers=doctor_auth,
        )
        assert res.status_code == 200
        body = res.json()
        assert 0.0 <= body["probability"] <= 1.0
        assert "shap" in body
        assert "lime" in body


def test_diabetes_prediction_admin_authorized(admin_auth) -> None:
    with TestClient(app) as client:
        res = client.post(
            DIABETES_URL,
            json={"patient": FULL_DIABETES_PATIENT},
            headers=admin_auth,
        )
        assert res.status_code == 200
        body = res.json()
        assert 0.0 <= body["probability"] <= 1.0


# ---------------------------------------------------------------------------
# Public Endpoints Verification Tests
# ---------------------------------------------------------------------------


def test_health_and_metadata_endpoints_remain_public() -> None:
    with TestClient(app) as client:
        # Health endpoints
        assert client.get("/api/v1/health").status_code == 200
        assert client.get("/api/v1/health/db").status_code == 200

        # Heart metadata
        assert client.get("/api/v1/heart/features").status_code == 200
        assert client.get("/api/v1/heart/models").status_code == 200

        # Diabetes metadata
        assert client.get("/api/v1/diabetes/features").status_code == 200
        assert client.get("/api/v1/diabetes/models").status_code == 200
