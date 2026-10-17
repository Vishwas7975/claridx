"""Tests for authentication endpoints and dependencies: login, /auth/me, tokens."""

from datetime import UTC, datetime, timedelta

import jwt
import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.core.security import create_access_token, hash_password
from app.main import app
from app.models import User, UserRole

AUTH_LOGIN_URL = "/api/v1/auth/login"
AUTH_ME_URL = "/api/v1/auth/me"
PLAIN_PASSWORD = "StrongDoctorPassword123!"


@pytest.fixture
def auth_user():
    """Create a persistent test user in the test database and ensure clean teardown."""
    with SessionLocal() as db:
        # Cleanup any collision
        existing = db.query(User).filter_by(email="test_doctor@example.com").first()
        if existing:
            db.delete(existing)
            db.commit()

        user = User(
            email="test_doctor@example.com",
            full_name="Dr. Test Physician",
            hashed_password=hash_password(PLAIN_PASSWORD),
            role=UserRole.DOCTOR,
            is_active=True,
            last_login_at=None,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        user_id = user.id

    yield user

    with SessionLocal() as db:
        u = db.get(User, user_id)
        if u:
            db.delete(u)
            db.commit()


@pytest.fixture
def inactive_user():
    """Create an inactive test user in the test database and ensure clean teardown."""
    with SessionLocal() as db:
        existing = db.query(User).filter_by(email="inactive_doctor@example.com").first()
        if existing:
            db.delete(existing)
            db.commit()

        user = User(
            email="inactive_doctor@example.com",
            full_name="Dr. Inactive Physician",
            hashed_password=hash_password(PLAIN_PASSWORD),
            role=UserRole.DOCTOR,
            is_active=False,
            last_login_at=None,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        user_id = user.id

    yield user

    with SessionLocal() as db:
        u = db.get(User, user_id)
        if u:
            db.delete(u)
            db.commit()


def test_login_success_updates_last_login_at_and_returns_bearer_token(auth_user) -> None:
    with TestClient(app) as client:
        res = client.post(
            AUTH_LOGIN_URL,
            json={"email": auth_user.email, "password": PLAIN_PASSWORD},
        )
        assert res.status_code == 200
        data = res.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

        # Verify DB was updated
        with SessionLocal() as db:
            refreshed = db.get(User, auth_user.id)
            assert refreshed is not None
            assert refreshed.last_login_at is not None
            # Must be within the last minute
            diff = datetime.now(UTC) - refreshed.last_login_at.replace(tzinfo=UTC)
            assert diff.total_seconds() < 60


def test_login_wrong_password_returns_generic_401_and_preserves_last_login(auth_user) -> None:
    with TestClient(app) as client:
        res = client.post(
            AUTH_LOGIN_URL,
            json={"email": auth_user.email, "password": "WrongPassword999!"},
        )
        assert res.status_code == 401
        assert res.json() == {"detail": "Incorrect email or password"}
        assert "Bearer" in res.headers.get("WWW-Authenticate", "")

        # Verify last_login_at was not updated
        with SessionLocal() as db:
            refreshed = db.get(User, auth_user.id)
            assert refreshed is not None
            assert refreshed.last_login_at is None


def test_login_unknown_email_returns_identical_generic_401() -> None:
    with TestClient(app) as client:
        res = client.post(
            AUTH_LOGIN_URL,
            json={"email": "nonexistent_email@example.com", "password": "AnyPassword123!"},
        )
        assert res.status_code == 401
        assert res.json() == {"detail": "Incorrect email or password"}
        assert "Bearer" in res.headers.get("WWW-Authenticate", "")


def test_login_inactive_user_returns_401_and_preserves_last_login(inactive_user) -> None:
    with TestClient(app) as client:
        res = client.post(
            AUTH_LOGIN_URL,
            json={"email": inactive_user.email, "password": PLAIN_PASSWORD},
        )
        assert res.status_code == 401
        assert res.json() == {"detail": "Inactive user account"}
        assert "Bearer" in res.headers.get("WWW-Authenticate", "")

        with SessionLocal() as db:
            refreshed = db.get(User, inactive_user.id)
            assert refreshed is not None
            assert refreshed.last_login_at is None


def test_login_supports_username_alias_and_case_insensitivity(auth_user) -> None:
    with TestClient(app) as client:
        # Uses 'username' field with mixed case and leading/trailing whitespace
        res = client.post(
            AUTH_LOGIN_URL,
            json={"username": f"  {auth_user.email.upper()}  ", "password": PLAIN_PASSWORD},
        )
        assert res.status_code == 200
        assert "access_token" in res.json()


def test_login_rejects_empty_password() -> None:
    with TestClient(app) as client:
        res = client.post(
            AUTH_LOGIN_URL,
            json={"email": "doctor@example.com", "password": ""},
        )
        assert res.status_code == 422


def test_auth_me_returns_safe_user_profile(auth_user) -> None:
    with TestClient(app) as client:
        # Login first to get valid token
        login_res = client.post(
            AUTH_LOGIN_URL,
            json={"email": auth_user.email, "password": PLAIN_PASSWORD},
        )
        token = login_res.json()["access_token"]

        me_res = client.get(
            AUTH_ME_URL,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert me_res.status_code == 200
        profile = me_res.json()

        assert profile["id"] == auth_user.id
        assert profile["email"] == auth_user.email
        assert profile["full_name"] == auth_user.full_name
        assert profile["role"] == "doctor"
        assert profile["is_active"] is True
        assert profile["last_login_at"] is not None
        assert "created_at" in profile
        assert "updated_at" in profile


def test_auth_endpoints_never_disclose_hashed_password(auth_user) -> None:
    with TestClient(app) as client:
        login_res = client.post(
            AUTH_LOGIN_URL,
            json={"email": auth_user.email, "password": PLAIN_PASSWORD},
        )
        assert "hashed_password" not in login_res.json()
        assert "password" not in login_res.json()

        token = login_res.json()["access_token"]
        me_res = client.get(
            AUTH_ME_URL,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert "hashed_password" not in me_res.json()
        assert "password" not in me_res.json()


def test_auth_me_missing_bearer_token() -> None:
    with TestClient(app) as client:
        res = client.get(AUTH_ME_URL)
        assert res.status_code == 401
        assert res.json() == {"detail": "Not authenticated"}
        assert "Bearer" in res.headers.get("WWW-Authenticate", "")


def test_auth_me_invalid_bearer_token() -> None:
    with TestClient(app) as client:
        res = client.get(AUTH_ME_URL, headers={"Authorization": "Bearer invalid.jwt.token"})
        assert res.status_code == 401
        assert res.json() == {"detail": "Could not validate credentials"}
        assert "Bearer" in res.headers.get("WWW-Authenticate", "")


def test_auth_me_expired_bearer_token(auth_user) -> None:
    expired_token = create_access_token(
        subject=auth_user.id,
        expires_delta=timedelta(seconds=-10),
    )
    with TestClient(app) as client:
        res = client.get(AUTH_ME_URL, headers={"Authorization": f"Bearer {expired_token}"})
        assert res.status_code == 401
        assert res.json() == {"detail": "Could not validate credentials"}
        assert "Bearer" in res.headers.get("WWW-Authenticate", "")


def test_auth_me_tampered_bearer_token(auth_user) -> None:
    token = create_access_token(subject=auth_user.id)
    tampered = token[:-5] + "xxxxx"
    with TestClient(app) as client:
        res = client.get(AUTH_ME_URL, headers={"Authorization": f"Bearer {tampered}"})
        assert res.status_code == 401
        assert res.json() == {"detail": "Could not validate credentials"}
        assert "Bearer" in res.headers.get("WWW-Authenticate", "")


def test_auth_me_non_existent_user_in_token() -> None:
    # Valid signed token with a user ID that does not exist in DB
    ghost_token = create_access_token(subject=9876543)
    with TestClient(app) as client:
        res = client.get(AUTH_ME_URL, headers={"Authorization": f"Bearer {ghost_token}"})
        assert res.status_code == 401
        assert res.json() == {"detail": "Could not validate credentials"}
        assert "Bearer" in res.headers.get("WWW-Authenticate", "")


def test_auth_me_rejects_inactive_user_with_previously_issued_token(auth_user) -> None:
    # Obtain token while user is active
    token = create_access_token(subject=auth_user.id)

    # Deactivate user in database
    with SessionLocal() as db:
        u = db.get(User, auth_user.id)
        assert u is not None
        u.is_active = False
        db.commit()

    # Previously issued token must now be rejected
    with TestClient(app) as client:
        res = client.get(AUTH_ME_URL, headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 401
        assert res.json() == {"detail": "Inactive user account"}
        assert "Bearer" in res.headers.get("WWW-Authenticate", "")


def test_auth_me_rejects_token_with_boolean_timestamp() -> None:
    settings = get_settings()
    # Signed token with invalid claim type (iat: False)
    token = jwt.encode(
        {"sub": "42", "exp": 9999999999, "iat": False, "type": "access"},
        settings.secret_key,
        algorithm=settings.jwt_algorithm,
    )
    with TestClient(app) as client:
        res = client.get(AUTH_ME_URL, headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 401
        assert res.json() == {"detail": "Could not validate credentials"}
        assert "Bearer" in res.headers.get("WWW-Authenticate", "")


def test_login_db_commit_failure_prevents_token_issuance(auth_user, monkeypatch) -> None:
    from sqlalchemy.orm import Session

    def broken_commit(self):
        raise RuntimeError("Database transaction failed")

    monkeypatch.setattr(Session, "commit", broken_commit)

    exc_match = "Database transaction failed"
    with TestClient(app) as client, pytest.raises(RuntimeError, match=exc_match):
        client.post(
            AUTH_LOGIN_URL,
            json={"email": auth_user.email, "password": PLAIN_PASSWORD},
        )


# ─── Form-encoded (OAuth2 Password flow) login tests ───────────────────────


def test_login_form_encoded_success_returns_bearer_token(auth_user) -> None:
    with TestClient(app) as client:
        res = client.post(
            AUTH_LOGIN_URL,
            data={"username": auth_user.email, "password": PLAIN_PASSWORD},
        )
        assert res.status_code == 200
        data = res.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"


def test_login_form_encoded_wrong_password_returns_generic_401(auth_user) -> None:
    with TestClient(app) as client:
        res = client.post(
            AUTH_LOGIN_URL,
            data={"username": auth_user.email, "password": "WrongPassword999!"},
        )
        assert res.status_code == 401
        assert res.json() == {"detail": "Incorrect email or password"}
        assert "Bearer" in res.headers.get("WWW-Authenticate", "")


def test_login_form_encoded_unknown_email_returns_generic_401() -> None:
    with TestClient(app) as client:
        res = client.post(
            AUTH_LOGIN_URL,
            data={"username": "ghost@example.com", "password": "AnyPassword123!"},
        )
        assert res.status_code == 401
        assert res.json() == {"detail": "Incorrect email or password"}
        assert "Bearer" in res.headers.get("WWW-Authenticate", "")


def test_login_form_encoded_inactive_user_returns_401(inactive_user) -> None:
    with TestClient(app) as client:
        res = client.post(
            AUTH_LOGIN_URL,
            data={"username": inactive_user.email, "password": PLAIN_PASSWORD},
        )
        assert res.status_code == 401
        assert res.json() == {"detail": "Inactive user account"}
        assert "Bearer" in res.headers.get("WWW-Authenticate", "")


def test_login_form_encoded_missing_fields_returns_422() -> None:
    with TestClient(app) as client:
        # No password field
        res = client.post(AUTH_LOGIN_URL, data={"username": "someone@example.com"})
        assert res.status_code == 422

        # No username field
        res2 = client.post(AUTH_LOGIN_URL, data={"password": "somepassword"})
        assert res2.status_code == 422


def test_login_form_updates_last_login_at(auth_user) -> None:
    with TestClient(app) as client:
        res = client.post(
            AUTH_LOGIN_URL,
            data={"username": auth_user.email, "password": PLAIN_PASSWORD},
        )
        assert res.status_code == 200

        with SessionLocal() as db:
            refreshed = db.get(User, auth_user.id)
            assert refreshed is not None
            assert refreshed.last_login_at is not None
            diff = datetime.now(UTC) - refreshed.last_login_at.replace(tzinfo=UTC)
            assert diff.total_seconds() < 60


def test_form_and_json_login_both_return_identical_response_shape(auth_user) -> None:
    with TestClient(app) as client:
        json_res = client.post(
            AUTH_LOGIN_URL,
            json={"email": auth_user.email, "password": PLAIN_PASSWORD},
        )
        form_res = client.post(
            AUTH_LOGIN_URL,
            data={"username": auth_user.email, "password": PLAIN_PASSWORD},
        )
        assert json_res.status_code == form_res.status_code == 200
        assert set(json_res.json().keys()) == set(form_res.json().keys())
        assert json_res.json()["token_type"] == form_res.json()["token_type"] == "bearer"


def test_login_unsupported_content_type_returns_415(auth_user) -> None:
    with TestClient(app) as client:
        # XML content type
        res_xml = client.post(
            AUTH_LOGIN_URL,
            content=b"<auth><email>test_doctor@example.com</email></auth>",
            headers={"Content-Type": "application/xml"},
        )
        assert res_xml.status_code == 415
        assert "Unsupported Content-Type" in res_xml.json()["detail"]

        # text/plain
        res_text = client.post(
            AUTH_LOGIN_URL,
            content=b"test_doctor@example.com:password",
            headers={"Content-Type": "text/plain"},
        )
        assert res_text.status_code == 415

        # application/octet-stream
        res_bin = client.post(
            AUTH_LOGIN_URL,
            content=b"\x00\x01\x02",
            headers={"Content-Type": "application/octet-stream"},
        )
        assert res_bin.status_code == 415

        # multipart/form-data
        res_multipart = client.post(
            AUTH_LOGIN_URL,
            files={"username": (None, "test_doctor@example.com"), "password": (None, "pw")},
        )
        assert res_multipart.status_code == 415
        assert "Unsupported Content-Type" in res_multipart.json()["detail"]


def test_login_uppercase_and_parameterized_content_types_handled(auth_user) -> None:
    with TestClient(app) as client:
        # Uppercase application/json with charset parameter
        res_json = client.post(
            AUTH_LOGIN_URL,
            content=f'{{"email": "{auth_user.email}", "password": "{PLAIN_PASSWORD}"}}'.encode(),
            headers={"Content-Type": "APPLICATION/JSON; charset=utf-8"},
        )
        assert res_json.status_code == 200
        assert res_json.json()["token_type"] == "bearer"

        # Uppercase application/x-www-form-urlencoded
        res_form = client.post(
            AUTH_LOGIN_URL,
            content=f"username={auth_user.email}&password={PLAIN_PASSWORD}".encode(),
            headers={"Content-Type": "APPLICATION/X-WWW-FORM-URLENCODED; charset=utf-8"},
        )
        assert res_form.status_code == 200
        assert res_form.json()["token_type"] == "bearer"


def test_login_malformed_json_and_shapes_return_422() -> None:
    with TestClient(app) as client:
        # Malformed JSON syntax
        res_syntax = client.post(
            AUTH_LOGIN_URL,
            content=b"{invalid json syntax",
            headers={"Content-Type": "application/json"},
        )
        assert res_syntax.status_code == 422
        assert "valid JSON" in res_syntax.json()["detail"]

        # Invalid shape: array instead of object
        res_array = client.post(
            AUTH_LOGIN_URL,
            content=b'["email", "password"]',
            headers={"Content-Type": "application/json"},
        )
        assert res_array.status_code == 422

        # Invalid shape: primitive instead of object
        res_prim = client.post(
            AUTH_LOGIN_URL,
            content=b'"just a string"',
            headers={"Content-Type": "application/json"},
        )
        assert res_prim.status_code == 422


def test_login_missing_content_type_returns_415(auth_user) -> None:
    with TestClient(app) as client:
        # Explicit empty Content-Type header
        res_empty = client.post(
            AUTH_LOGIN_URL,
            content=f'{{"email": "{auth_user.email}", "password": "{PLAIN_PASSWORD}"}}'.encode(),
            headers={"Content-Type": ""},
        )
        assert res_empty.status_code == 415
        assert "Content-Type header is required" in res_empty.json()["detail"]

        # Completely absent Content-Type header
        res_absent = client.post(
            AUTH_LOGIN_URL,
            content=f'{{"email": "{auth_user.email}", "password": "{PLAIN_PASSWORD}"}}'.encode(),
        )
        assert res_absent.status_code == 415
        assert "Content-Type header is required" in res_absent.json()["detail"]
