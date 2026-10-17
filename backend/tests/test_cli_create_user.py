"""Tests for the secure user provisioning CLI command (app.cli.create_user)."""

from unittest.mock import MagicMock

import pytest
from sqlalchemy import select

from app.cli.create_user import (
    ProvisioningError,
    main,
    provision_user,
    validate_email,
    validate_role,
)
from app.core.database import SessionLocal
from app.core.security import verify_password
from app.models.user import User, UserRole

PLAIN_PASSWORD = "StrongPassword123!"


@pytest.fixture(autouse=True)
def cleanup_cli_test_users():
    """Ensure test users are cleaned up before and after each test."""
    test_emails = [
        "cli_doc@example.com",
        "cli_admin@example.com",
        "cli_researcher@example.com",
        "cli_dup@example.com",
        "cli_interactive@example.com",
        "cli_failed@example.com",
    ]
    with SessionLocal() as db:
        for email in test_emails:
            u = db.scalars(select(User).where(User.email == email)).first()
            if u:
                db.delete(u)
        db.commit()

    yield

    with SessionLocal() as db:
        for email in test_emails:
            u = db.scalars(select(User).where(User.email == email)).first()
            if u:
                db.delete(u)
        db.commit()


def test_validate_email() -> None:
    assert validate_email("  Test.User+Tag@Example.COM  ") == "test.user+tag@example.com"
    assert validate_email("doctor@sub.domain.com") == "doctor@sub.domain.com"
    assert validate_email("user@med.hospital.org") == "user@med.hospital.org"

    invalid_emails = (
        "",
        "   ",
        "notanemail",
        "user@",
        "@domain.com",
        "user@domain",
        "a" * 256 + "@b.com",
    )
    for invalid in invalid_emails:
        with pytest.raises(ProvisioningError):
            validate_email(invalid)


def test_validate_role() -> None:
    assert validate_role("admin") == UserRole.ADMIN
    assert validate_role("ADMIN") == UserRole.ADMIN
    assert validate_role("doctor") == UserRole.DOCTOR
    assert validate_role("Doctor") == UserRole.DOCTOR
    assert validate_role("researcher") == UserRole.RESEARCHER
    assert validate_role("  RESEARCHER  ") == UserRole.RESEARCHER

    for invalid in ("superuser", "patient", "guest", "", "root"):
        with pytest.raises(ProvisioningError):
            validate_role(invalid)


def test_successful_creation_of_doctor() -> None:
    with SessionLocal() as db:
        user = provision_user(
            db,
            email="cli_doc@example.com",
            full_name="Dr. CLI Doctor",
            role_str="doctor",
            password=PLAIN_PASSWORD,
            confirm_password=PLAIN_PASSWORD,
        )
        assert user.id is not None
        assert user.email == "cli_doc@example.com"
        assert user.role == UserRole.DOCTOR
        assert user.is_active is True
        assert user.hashed_password != PLAIN_PASSWORD
        assert user.hashed_password.startswith("$argon2id$")
        assert verify_password(PLAIN_PASSWORD, user.hashed_password) is True
        assert verify_password("WrongPassword!", user.hashed_password) is False


def test_successful_creation_of_researcher() -> None:
    with SessionLocal() as db:
        user = provision_user(
            db,
            email="cli_researcher@example.com",
            full_name="Dr. Clinical Researcher",
            role_str="researcher",
            password=PLAIN_PASSWORD,
            confirm_password=PLAIN_PASSWORD,
        )
        assert user.role == UserRole.RESEARCHER
        assert verify_password(PLAIN_PASSWORD, user.hashed_password) is True


def test_successful_creation_of_admin_with_explicit_confirmation() -> None:
    # 1. Via confirm_admin flag
    with SessionLocal() as db:
        user = provision_user(
            db,
            email="cli_admin@example.com",
            full_name="Sys Admin",
            role_str="admin",
            password=PLAIN_PASSWORD,
            confirm_password=PLAIN_PASSWORD,
            confirm_admin=True,
        )
        assert user.role == UserRole.ADMIN
        assert verify_password(PLAIN_PASSWORD, user.hashed_password) is True

    # Cleanup for next test
    with SessionLocal() as db:
        u = db.scalars(select(User).where(User.email == "cli_admin@example.com")).first()
        if u:
            db.delete(u)
            db.commit()

    # 2. Via interactive admin_confirm_func answering "y"
    with SessionLocal() as db:
        user = provision_user(
            db,
            email="cli_admin@example.com",
            full_name="Sys Admin",
            role_str="admin",
            password=PLAIN_PASSWORD,
            confirm_password=PLAIN_PASSWORD,
            confirm_admin=False,
            admin_confirm_func=lambda prompt: "y",
        )
        assert user.role == UserRole.ADMIN


def test_admin_creation_aborted_when_confirmation_declined() -> None:
    with SessionLocal() as db:
        # Prompt answered with "no"
        with pytest.raises(ProvisioningError, match="cancelled"):
            provision_user(
                db,
                email="cli_admin@example.com",
                full_name="Sys Admin",
                role_str="admin",
                password=PLAIN_PASSWORD,
                confirm_password=PLAIN_PASSWORD,
                confirm_admin=False,
                admin_confirm_func=lambda prompt: "n",
            )

        # Confirm user was not created
        assert db.scalars(select(User).where(User.email == "cli_admin@example.com")).first() is None


def test_admin_creation_fails_if_no_confirmation_method() -> None:
    with (
        SessionLocal() as db,
        pytest.raises(ProvisioningError, match="requires explicit confirmation"),
    ):
        provision_user(
            db,
            email="cli_admin@example.com",
            full_name="Sys Admin",
            role_str="admin",
            password=PLAIN_PASSWORD,
            confirm_password=PLAIN_PASSWORD,
            confirm_admin=False,
            admin_confirm_func=None,
        )


def test_password_mismatch_rejected() -> None:
    with SessionLocal() as db:
        with pytest.raises(ProvisioningError, match="Passwords do not match"):
            provision_user(
                db,
                email="cli_doc@example.com",
                full_name="Dr. Test",
                role_str="doctor",
                password="Password123!",
                confirm_password="PasswordMismatch!",
            )
        assert db.scalars(select(User).where(User.email == "cli_doc@example.com")).first() is None


def test_empty_password_rejected() -> None:
    with SessionLocal() as db, pytest.raises(ProvisioningError, match="Password cannot be empty"):
        provision_user(
            db,
            email="cli_doc@example.com",
            full_name="Dr. Test",
            role_str="doctor",
            password="",
            confirm_password="",
        )


def test_duplicate_email_rejected_and_never_overwrites_or_elevates() -> None:
    with SessionLocal() as db:
        # Create initial researcher
        initial = provision_user(
            db,
            email="cli_dup@example.com",
            full_name="Original Researcher",
            role_str="researcher",
            password=PLAIN_PASSWORD,
            confirm_password=PLAIN_PASSWORD,
        )
        initial_id = initial.id
        initial_hash = initial.hashed_password

        # Attempt to provision same email as admin
        with pytest.raises(ProvisioningError, match="already exists"):
            provision_user(
                db,
                email="cli_dup@example.com",
                full_name="Impostor Admin",
                role_str="admin",
                password="NewPassword123!",
                confirm_password="NewPassword123!",
                confirm_admin=True,
            )

        # Verify initial user is completely unmodified
        db.expire_all()
        persisted = db.get(User, initial_id)
        assert persisted is not None
        assert persisted.full_name == "Original Researcher"
        assert persisted.role == UserRole.RESEARCHER
        assert persisted.hashed_password == initial_hash


def test_database_failure_handling_rolls_back() -> None:
    mock_db = MagicMock(spec=SessionLocal())
    mock_db.scalars.return_value.first.return_value = None
    mock_db.commit.side_effect = RuntimeError("DB connection dropped")

    with pytest.raises(ProvisioningError, match="Database error"):
        provision_user(
            mock_db,
            email="cli_failed@example.com",
            full_name="Failed User",
            role_str="doctor",
            password=PLAIN_PASSWORD,
            confirm_password=PLAIN_PASSWORD,
        )

    mock_db.rollback.assert_called_once()


def test_cli_main_interactive_success(monkeypatch, capsys) -> None:
    inputs = {
        "Email address: ": "cli_interactive@example.com",
        "Full name: ": "Interactive Doctor",
        "Role (admin, doctor, researcher): ": "doctor",
    }
    passwords = [PLAIN_PASSWORD, PLAIN_PASSWORD]

    def mock_input(prompt: str) -> str:
        return inputs[prompt]

    def mock_getpass(prompt: str) -> str:
        return passwords.pop(0)

    exit_code = main([], input_func=mock_input, getpass_func=mock_getpass)
    assert exit_code == 0

    captured = capsys.readouterr()
    assert "User successfully created!" in captured.out
    assert "cli_interactive@example.com" in captured.out
    assert "doctor" in captured.out
    # Guarantee no passwords or hashes leak to stdout or stderr
    assert PLAIN_PASSWORD not in captured.out
    assert PLAIN_PASSWORD not in captured.err
    assert "$argon2id$" not in captured.out
    assert "$argon2id$" not in captured.err


def test_cli_main_validation_failure_exits_with_code_1(capsys) -> None:
    exit_code = main(
        ["--email", "invalid_email", "--full-name", "Doc", "--role", "doctor"],
        getpass_func=lambda prompt: PLAIN_PASSWORD,
    )
    assert exit_code == 1

    captured = capsys.readouterr()
    assert "Error: Invalid email address format" in captured.err
    assert PLAIN_PASSWORD not in captured.err


def test_cli_main_cancellation_exits_with_code_130(capsys) -> None:
    def raise_interrupt(prompt: str) -> str:
        raise KeyboardInterrupt()

    exit_code = main([], input_func=raise_interrupt)
    assert exit_code == 130

    captured = capsys.readouterr()
    assert "Operation cancelled" in captured.err
