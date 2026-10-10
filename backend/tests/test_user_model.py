import pytest
from sqlalchemy import inspect
from sqlalchemy.exc import IntegrityError

from app.core.database import SessionLocal, engine
from app.models import User, UserRole


def test_users_table_has_expected_columns() -> None:
    inspector = inspect(engine)
    assert "users" in inspector.get_table_names()
    columns = {column["name"] for column in inspector.get_columns("users")}
    assert columns >= {
        "id",
        "email",
        "full_name",
        "hashed_password",
        "role",
        "is_active",
        "last_login_at",
        "created_at",
        "updated_at",
    }


def test_email_must_be_unique() -> None:
    with SessionLocal() as db:
        db.add(
            User(email="a@example.com", full_name="A", hashed_password="x", role=UserRole.DOCTOR)
        )
        db.flush()
        db.add(User(email="a@example.com", full_name="B", hashed_password="y", role=UserRole.ADMIN))
        with pytest.raises(IntegrityError):
            db.flush()
        db.rollback()  # nothing is ever committed by this test
