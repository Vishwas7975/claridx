from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.database import SessionLocal
from app.core.security import decode_access_token, verify_password
from app.main import app
from app.models.user import User, UserRole


def test_register_success():
    email = "newpatient_1@example.com"
    with SessionLocal() as db:
        old = db.scalar(select(User).where(User.email == email))
        if old:
            db.delete(old)
            db.commit()

    with TestClient(app) as client:
        payload = {
            "email": email,
            "full_name": "New Patient",
            "password": "SecurePassword123!",
            "confirm_password": "SecurePassword123!",
        }
        response = client.post("/api/v1/auth/register", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

        token_payload = decode_access_token(data["access_token"])
        with SessionLocal() as db:
            user = db.scalar(select(User).where(User.id == token_payload.user_id))
            assert user is not None
            assert user.email == email
            assert user.full_name == "New Patient"
            assert user.role == UserRole.PATIENT
            assert user.is_active is True
            assert user.hashed_password != "SecurePassword123!"
            assert verify_password("SecurePassword123!", user.hashed_password)
            db.delete(user)
            db.commit()


def test_register_duplicate_email():
    email = "duplicate_test@example.com"
    with SessionLocal() as db:
        old = db.scalar(select(User).where(User.email == email))
        if old:
            db.delete(old)
            db.commit()

    with TestClient(app) as client:
        payload = {
            "email": email,
            "full_name": "First Patient",
            "password": "SecurePassword123!",
            "confirm_password": "SecurePassword123!",
        }
        res1 = client.post("/api/v1/auth/register", json=payload)
        assert res1.status_code == 201

        # Second registration with uppercase email variation
        payload["email"] = email.upper()
        res2 = client.post("/api/v1/auth/register", json=payload)
        assert res2.status_code == 409
        assert "already exists" in res2.json()["detail"].lower()

    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.email == email))
        if user:
            db.delete(user)
            db.commit()


def test_register_password_mismatch():
    with TestClient(app) as client:
        payload = {
            "email": "mismatch@example.com",
            "full_name": "Mismatch User",
            "password": "SecurePassword123!",
            "confirm_password": "DifferentPassword123!",
        }
        response = client.post("/api/v1/auth/register", json=payload)
        assert response.status_code == 422


def test_register_password_too_short():
    with TestClient(app) as client:
        payload = {
            "email": "short@example.com",
            "full_name": "Short Password",
            "password": "short",
            "confirm_password": "short",
        }
        response = client.post("/api/v1/auth/register", json=payload)
        assert response.status_code == 422


def test_register_invalid_email():
    with TestClient(app) as client:
        payload = {
            "email": "not-an-email",
            "full_name": "Bad Email",
            "password": "SecurePassword123!",
            "confirm_password": "SecurePassword123!",
        }
        response = client.post("/api/v1/auth/register", json=payload)
        assert response.status_code == 422


def test_register_ignores_client_supplied_role():
    email = "attacker_test@example.com"
    with SessionLocal() as db:
        old = db.scalar(select(User).where(User.email == email))
        if old:
            db.delete(old)
            db.commit()

    with TestClient(app) as client:
        payload = {
            "email": email,
            "full_name": "Privilege Escalation Attempt",
            "password": "SecurePassword123!",
            "confirm_password": "SecurePassword123!",
            "role": "admin",
        }
        response = client.post("/api/v1/auth/register", json=payload)
        assert response.status_code == 201

        token_payload = decode_access_token(response.json()["access_token"])
        with SessionLocal() as db:
            user = db.scalar(select(User).where(User.id == token_payload.user_id))
            assert user is not None
            assert user.role == UserRole.PATIENT
            db.delete(user)
            db.commit()


def test_register_then_login_and_access_profile():
    email = "flow_patient@example.com"
    with SessionLocal() as db:
        old = db.scalar(select(User).where(User.email == email))
        if old:
            db.delete(old)
            db.commit()

    with TestClient(app) as client:
        reg_payload = {
            "email": email,
            "full_name": "Flow Patient",
            "password": "ValidPassword999!",
            "confirm_password": "ValidPassword999!",
        }
        reg_res = client.post("/api/v1/auth/register", json=reg_payload)
        assert reg_res.status_code == 201
        token = reg_res.json()["access_token"]

        # Verify /me endpoint works with returned registration token
        me_res = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert me_res.status_code == 200
        profile = me_res.json()
        assert profile["email"] == email
        assert profile["role"] == "patient"
        assert profile["full_name"] == "Flow Patient"

        # Verify user can log in with their credentials
        login_res = client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": "ValidPassword999!"},
        )
        assert login_res.status_code == 200
        assert "access_token" in login_res.json()

    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.email == email))
        if user:
            db.delete(user)
            db.commit()
