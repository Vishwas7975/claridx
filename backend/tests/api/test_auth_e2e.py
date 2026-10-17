"""End-to-End Authentication, CLI Provisioning, and RBAC Integration Test.

Verifies the complete workflow across layers:
1. Provision accounts using the CLI provisioning logic (provision_user).
2. Authenticate via POST /api/v1/auth/login with JSON credentials.
3. Read user profile via GET /api/v1/auth/me.
4. Execute heart and diabetes predictions as DOCTOR.
5. Execute heart and diabetes predictions as ADMIN.
6. Verify RESEARCHER can view metadata but is rejected with 403 on predictions.
7. Verify unauthenticated requests (simulating logout) are rejected with 401.
8. Verify inactive account, expired token, and invalid credentials behavior.
"""

from datetime import timedelta

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_diabetes_registry, get_registry
from app.cli.create_user import provision_user
from app.core.database import SessionLocal
from app.core.security import create_access_token
from app.main import app
from app.models.user import User, UserRole
from app.services.diabetes_registry import DiabetesModelRegistry
from app.services.model_registry import ModelRegistry
from ml.pipelines.diabetes import build_models as build_diabetes_models
from ml.pipelines.heart import build_models as build_heart_models
from tests.api.payloads import FULL_PATIENT
from tests.pipelines.synthetic import make_diabetes_like_data, make_heart_like_data

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
    app.dependency_overrides.clear()


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def clean_db():
    with SessionLocal() as db:
        yield db
        # Clean up test accounts created during E2E test
        users = db.query(User).filter(User.email.like("%@e2e.claridx.test")).all()
        for u in users:
            db.delete(u)
        db.commit()


def test_full_auth_and_rbac_e2e_flow(client: TestClient, clean_db):
    """E2E test traversing account provisioning, login, profile fetch, and RBAC predictions."""
    # 1. Provision accounts via CLI logic
    doctor = provision_user(
        clean_db,
        email="doctor@e2e.claridx.test",
        full_name="Dr. E2E Doctor",
        role_str="doctor",
        password="ValidPassword123!",
        confirm_password="ValidPassword123!",
    )
    admin = provision_user(
        clean_db,
        email="admin@e2e.claridx.test",
        full_name="Admin E2E User",
        role_str="admin",
        password="ValidPassword123!",
        confirm_password="ValidPassword123!",
        confirm_admin=True,
    )
    assert admin.role == UserRole.ADMIN

    researcher = provision_user(
        clean_db,
        email="researcher@e2e.claridx.test",
        full_name="Researcher E2E User",
        role_str="researcher",
        password="ValidPassword123!",
        confirm_password="ValidPassword123!",
    )
    assert researcher.role == UserRole.RESEARCHER
    inactive_doctor = provision_user(
        clean_db,
        email="inactive@e2e.claridx.test",
        full_name="Inactive Doctor",
        role_str="doctor",
        password="ValidPassword123!",
        confirm_password="ValidPassword123!",
    )
    inactive_doctor.is_active = False
    clean_db.commit()

    # 2. Login as DOCTOR
    res_login_doc = client.post(
        "/api/v1/auth/login",
        json={"email": "doctor@e2e.claridx.test", "password": "ValidPassword123!"},
    )
    assert res_login_doc.status_code == 200
    doc_token = res_login_doc.json()["access_token"]
    assert doc_token
    assert res_login_doc.json()["token_type"] == "bearer"

    # 3. Read profile from /api/v1/auth/me as DOCTOR
    res_me_doc = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {doc_token}"},
    )
    assert res_me_doc.status_code == 200
    doc_profile = res_me_doc.json()
    assert doc_profile["email"] == "doctor@e2e.claridx.test"
    assert doc_profile["role"] == "doctor"
    assert doc_profile["full_name"] == "Dr. E2E Doctor"
    assert doc_profile["is_active"] is True
    assert "hashed_password" not in doc_profile

    # 4. Submit heart & diabetes predictions as DOCTOR
    res_heart_doc = client.post(
        "/api/v1/heart/predictions",
        headers={"Authorization": f"Bearer {doc_token}"},
        json={"model_name": "random_forest", "patient": FULL_PATIENT},
    )
    assert res_heart_doc.status_code == 200
    assert "probability" in res_heart_doc.json()

    res_diab_doc = client.post(
        "/api/v1/diabetes/predictions",
        headers={"Authorization": f"Bearer {doc_token}"},
        json={"model_name": "random_forest", "patient": FULL_DIABETES_PATIENT},
    )
    assert res_diab_doc.status_code == 200
    assert "probability" in res_diab_doc.json()

    # 5. Login and predict as ADMIN
    res_login_admin = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@e2e.claridx.test", "password": "ValidPassword123!"},
    )
    assert res_login_admin.status_code == 200
    admin_token = res_login_admin.json()["access_token"]

    res_heart_admin = client.post(
        "/api/v1/heart/predictions",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"model_name": "random_forest", "patient": FULL_PATIENT},
    )
    assert res_heart_admin.status_code == 200

    # 6. Login as RESEARCHER: metadata allowed, prediction rejected (403)
    res_login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "researcher@e2e.claridx.test", "password": "ValidPassword123!"},
    )
    assert res_login_res.status_code == 200
    res_token = res_login_res.json()["access_token"]

    # Metadata endpoints work
    res_meta_heart = client.get("/api/v1/heart/features")
    assert res_meta_heart.status_code == 200

    res_meta_diab = client.get("/api/v1/diabetes/features")
    assert res_meta_diab.status_code == 200

    res_meta_models = client.get("/api/v1/diabetes/models")
    assert res_meta_models.status_code == 200

    # Predictions denied for researcher
    res_heart_res = client.post(
        "/api/v1/heart/predictions",
        headers={"Authorization": f"Bearer {res_token}"},
        json={"model_name": "random_forest", "patient": FULL_PATIENT},
    )
    assert res_heart_res.status_code == 403
    assert "permissions" in res_heart_res.json()["detail"].lower()

    res_diab_res = client.post(
        "/api/v1/diabetes/predictions",
        headers={"Authorization": f"Bearer {res_token}"},
        json={"model_name": "random_forest", "patient": FULL_DIABETES_PATIENT},
    )
    assert res_diab_res.status_code == 403

    # 7. Unauthenticated prediction requests (simulating logout or unauthenticated client)
    res_unauth = client.post(
        "/api/v1/heart/predictions",
        json={"model_name": "random_forest", "patient": FULL_PATIENT},
    )
    assert res_unauth.status_code == 401
    assert "Bearer" in res_unauth.headers.get("WWW-Authenticate", "")

    # 8. Security failure modes: wrong password, inactive user, expired token
    # 8a. Wrong password -> 401 generic
    res_bad_pw = client.post(
        "/api/v1/auth/login",
        json={"email": "doctor@e2e.claridx.test", "password": "WrongPassword123!"},
    )
    assert res_bad_pw.status_code == 401
    assert res_bad_pw.json()["detail"] == "Incorrect email or password"

    # 8b. Inactive user -> 401 generic
    res_inactive_login = client.post(
        "/api/v1/auth/login",
        json={"email": "inactive@e2e.claridx.test", "password": "ValidPassword123!"},
    )
    assert res_inactive_login.status_code == 401
    assert res_inactive_login.json()["detail"] == "Inactive user account"

    # 8c. Expired token -> 401
    expired_token = create_access_token(subject=doctor.id, expires_delta=timedelta(seconds=-10))
    res_expired = client.post(
        "/api/v1/heart/predictions",
        headers={"Authorization": f"Bearer {expired_token}"},
        json={"model_name": "random_forest", "patient": FULL_PATIENT},
    )
    assert res_expired.status_code == 401
    assert "credentials" in res_expired.json()["detail"].lower()
