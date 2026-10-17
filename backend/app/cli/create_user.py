"""Secure CLI command for provisioning ClariDx user accounts.

Usage:
    python -m app.cli.create_user [--email EMAIL] [--full-name NAME] [--role ROLE] [--confirm-admin]

Passwords are NEVER accepted as command-line arguments to prevent leakage via
shell history and process table inspection. They are always prompted securely via getpass.
"""

from __future__ import annotations

import argparse
import getpass
import re
import sys
from collections.abc import Callable

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.user import User, UserRole

# Standard regex for email validation
_EMAIL_REGEX = re.compile(r"^[\w\.\+\-]+@([\w\-]+\.)+[a-zA-Z]{2,}$")

_ROLE_MAP: dict[str, UserRole] = {
    "admin": UserRole.ADMIN,
    "doctor": UserRole.DOCTOR,
    "researcher": UserRole.RESEARCHER,
}


class ProvisioningError(ValueError):
    """Raised when user provisioning validation fails."""


def validate_email(email: str) -> str:
    """Validate and normalize an email address."""
    clean = email.strip().lower()
    if not clean:
        raise ProvisioningError("Email address cannot be empty.")
    if len(clean) > 255:
        raise ProvisioningError("Email address must not exceed 255 characters.")
    if not _EMAIL_REGEX.match(clean):
        raise ProvisioningError(f"Invalid email address format: '{clean}'")
    return clean


def validate_role(role_input: str) -> UserRole:
    """Validate and map role input to a UserRole enum."""
    clean = role_input.strip().lower()
    if clean not in _ROLE_MAP:
        allowed = ", ".join(_ROLE_MAP.keys())
        raise ProvisioningError(f"Invalid role '{role_input}'. Allowed roles: {allowed}.")
    return _ROLE_MAP[clean]


def provision_user(
    db: Session,
    *,
    email: str,
    full_name: str,
    role_str: str,
    password: str,
    confirm_password: str,
    confirm_admin: bool = False,
    admin_confirm_func: Callable[[str], str] | None = None,
) -> User:
    """Validate inputs and provision a new user in the database.

    Guarantees:
    - No passwords or hashes logged or leaked.
    - No silent overwrites or role elevations of existing accounts.
    - Explicit confirmation required for ADMIN role.
    - Clean transaction rollback on failure.
    """
    clean_email = validate_email(email)

    clean_name = full_name.strip()
    if not clean_name:
        raise ProvisioningError("Full name cannot be empty.")
    if len(clean_name) > 150:
        raise ProvisioningError("Full name must not exceed 150 characters.")

    role = validate_role(role_str)

    # Check for existing account
    existing = db.scalars(select(User).where(User.email == clean_email)).first()
    if existing is not None:
        raise ProvisioningError(
            f"User with email '{clean_email}' already exists. Overwrite/elevation is forbidden."
        )

    # Admin confirmation check
    if role == UserRole.ADMIN and not confirm_admin:
        if admin_confirm_func is None:
            raise ProvisioningError(
                "Creating an administrator account requires explicit confirmation."
            )
        prompt_msg = (
            f"Are you sure you want to create an account with ADMIN privileges "
            f"for '{clean_email}'? [y/N]: "
        )
        response = admin_confirm_func(prompt_msg)
        if response.strip().lower() not in {"y", "yes"}:
            raise ProvisioningError("Administrator account creation was cancelled.")

    # Password validation
    if not password:
        raise ProvisioningError("Password cannot be empty.")
    if password != confirm_password:
        raise ProvisioningError("Passwords do not match.")

    hashed = hash_password(password)

    user = User(
        email=clean_email,
        full_name=clean_name,
        role=role,
        hashed_password=hashed,
        is_active=True,
    )

    try:
        db.add(user)
        db.commit()
        db.refresh(user)
    except Exception as exc:
        db.rollback()
        raise ProvisioningError(f"Database error during user creation: {exc}") from exc

    return user


def main(
    args: list[str] | None = None,
    *,
    input_func: Callable[[str], str] = input,
    getpass_func: Callable[[str], str] = getpass.getpass,
    db: Session | None = None,
) -> int:
    """CLI entrypoint for user provisioning."""
    parser = argparse.ArgumentParser(
        description="Securely create a ClariDx user account.",
        prog="python -m app.cli.create_user",
    )
    parser.add_argument("--email", help="User's email address")
    parser.add_argument("--full-name", help="User's full name")
    parser.add_argument(
        "--role",
        help="Role for the new account: admin, doctor, or researcher",
    )
    parser.add_argument(
        "--confirm-admin",
        action="store_true",
        help="Explicitly confirm administrator privileges non-interactively",
    )

    parsed = parser.parse_args(args)

    try:
        email = parsed.email
        if not email:
            email = input_func("Email address: ")

        full_name = parsed.full_name
        if not full_name:
            full_name = input_func("Full name: ")

        role_str = parsed.role
        if not role_str:
            role_str = input_func("Role (admin, doctor, researcher): ")

        password = getpass_func("Password: ")
        confirm_password = getpass_func("Confirm password: ")

        if db is not None:
            user = provision_user(
                db,
                email=email,
                full_name=full_name,
                role_str=role_str,
                password=password,
                confirm_password=confirm_password,
                confirm_admin=parsed.confirm_admin,
                admin_confirm_func=input_func,
            )
        else:
            with SessionLocal() as session:
                user = provision_user(
                    session,
                    email=email,
                    full_name=full_name,
                    role_str=role_str,
                    password=password,
                    confirm_password=confirm_password,
                    confirm_admin=parsed.confirm_admin,
                    admin_confirm_func=input_func,
                )
        print(
            f"User successfully created! ID: {user.id}, "
            f"Email: {user.email}, Role: {user.role.value}"
        )
        return 0
    except ProvisioningError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except (KeyboardInterrupt, EOFError):
        print("\nOperation cancelled.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    sys.exit(main())
