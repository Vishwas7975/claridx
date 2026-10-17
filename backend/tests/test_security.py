"""Focused unit tests for security primitives: password hashing, tokens, and settings."""

import time
from datetime import timedelta

import jwt
import pytest
from pydantic import ValidationError

from app.core.config import Settings, get_settings
from app.core.security import (
    ExpiredTokenError,
    InvalidTokenError,
    TokenError,
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_password_hash_verification_succeeds_for_correct_password() -> None:
    password = "CorrectHorseBatteryStaple123!"
    hashed = hash_password(password)
    assert verify_password(password, hashed) is True


def test_incorrect_passwords_fail_verification() -> None:
    password = "CorrectHorseBatteryStaple123!"
    hashed = hash_password(password)
    assert verify_password("WrongPassword123!", hashed) is False
    assert verify_password("", hashed) is False
    assert verify_password(password.lower(), hashed) is False


def test_stored_hashes_differ_from_plaintext_and_are_non_deterministic() -> None:
    password = "StrongPassword456$"
    h1 = hash_password(password)
    h2 = hash_password(password)

    # Hash must not contain plaintext
    assert password not in h1
    assert h1.startswith("$argon2id$")

    # Hashes of identical passwords must differ due to unique salts
    assert h1 != h2

    # Both hashes must still verify correctly
    assert verify_password(password, h1) is True
    assert verify_password(password, h2) is True


def test_malformed_or_unsupported_stored_hash_returns_false() -> None:
    # None of these should raise unhandled hashing library exceptions
    assert verify_password("password", "") is False
    assert verify_password("password", "not_a_hash") is False
    assert verify_password("password", "$argon2id$truncated") is False
    assert verify_password("password", "$unknown_algo$v=1$abc") is False
    assert verify_password("password", "plaintext_secret") is False


def test_valid_token_decodes_to_expected_subject() -> None:
    token = create_access_token(subject=42)
    payload = decode_access_token(token)

    assert payload.sub == "42"
    assert payload.user_id == 42
    assert payload.token_type == "access"
    assert payload.exp is not None
    assert payload.iat is not None


def test_valid_integer_string_subject_is_accepted() -> None:
    token = create_access_token(subject="105")
    payload = decode_access_token(token)
    assert payload.sub == "105"
    assert payload.user_id == 105


@pytest.mark.parametrize("invalid_subject", ["", "   ", "abc", "-5", 0, -1, None])
def test_invalid_subject_raises_value_error_on_creation(invalid_subject) -> None:
    with pytest.raises(ValueError):
        create_access_token(subject=invalid_subject)  # type: ignore[arg-type]


def test_expired_token_is_rejected() -> None:
    token = create_access_token(subject=10, expires_delta=timedelta(seconds=-1))
    with pytest.raises(ExpiredTokenError, match="Token has expired"):
        decode_access_token(token)


def test_malformed_token_is_rejected() -> None:
    with pytest.raises(InvalidTokenError):
        decode_access_token("this.is.not.a.valid.jwt")


def test_tampered_token_is_rejected() -> None:
    token = create_access_token(subject=99)
    tampered = token[:-5] + "aaaaa"
    with pytest.raises(InvalidTokenError):
        decode_access_token(tampered)


def test_incorrectly_signed_token_is_rejected() -> None:
    wrong_secret = "y" * 32
    token = jwt.encode(
        {"sub": "99", "exp": 9999999999, "iat": 1000000000, "type": "access"},
        wrong_secret,
        algorithm="HS256",
    )
    with pytest.raises(InvalidTokenError):
        decode_access_token(token)


def test_unsupported_algorithm_token_is_rejected() -> None:
    token = jwt.encode(
        {"sub": "99", "exp": 9999999999, "iat": 1000000000, "type": "access"},
        key="",
        algorithm="none",
    )
    with pytest.raises(InvalidTokenError):
        decode_access_token(token)


def test_token_missing_type_claim_is_rejected() -> None:
    settings = get_settings()
    now_ts = int(time.time())
    # Correctly signed, but missing the 'type' claim entirely
    token = jwt.encode(
        {"sub": "99", "exp": now_ts + 300, "iat": now_ts},
        settings.secret_key,
        algorithm=settings.jwt_algorithm,
    )
    with pytest.raises(InvalidTokenError, match="Invalid or missing token type claim"):
        decode_access_token(token)


def test_non_access_token_type_is_rejected() -> None:
    settings = get_settings()
    now_ts = int(time.time())
    token = jwt.encode(
        {"sub": "99", "exp": now_ts + 300, "iat": now_ts, "type": "refresh"},
        settings.secret_key,
        algorithm=settings.jwt_algorithm,
    )
    with pytest.raises(InvalidTokenError, match="Invalid or missing token type claim"):
        decode_access_token(token)


def test_out_of_range_timestamp_raises_invalid_token_error() -> None:
    settings = get_settings()
    # Signed token with an out-of-range timestamp
    token = jwt.encode(
        {"sub": "99", "exp": 10**14, "iat": 1000000000, "type": "access"},
        settings.secret_key,
        algorithm=settings.jwt_algorithm,
    )
    with pytest.raises(InvalidTokenError, match="Token timestamp claim is out of supported range"):
        decode_access_token(token)


def test_non_integer_subject_is_rejected_on_decode() -> None:
    settings = get_settings()
    now_ts = int(time.time())
    token = jwt.encode(
        {"sub": "not-an-integer-id", "exp": now_ts + 300, "iat": now_ts, "type": "access"},
        settings.secret_key,
        algorithm=settings.jwt_algorithm,
    )
    with pytest.raises(InvalidTokenError, match="valid integer user ID"):
        decode_access_token(token)


def test_settings_rejects_missing_or_short_secret_key() -> None:
    valid = Settings(database_url="mysql://dummy", secret_key="a" * 32)
    assert len(valid.secret_key) == 32

    with pytest.raises(ValidationError):
        Settings(database_url="mysql://dummy", secret_key="too-short")

    with pytest.raises(ValidationError):
        Settings(database_url="mysql://dummy", secret_key=None)  # type: ignore[arg-type]


def test_settings_rejects_unapproved_jwt_algorithm() -> None:
    with pytest.raises(ValidationError):
        Settings(database_url="mysql://dummy", secret_key="a" * 32, jwt_algorithm="none")  # type: ignore[arg-type]

    with pytest.raises(ValidationError):
        Settings(database_url="mysql://dummy", secret_key="a" * 32, jwt_algorithm="RS256")  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "invalid_exp",
    [
        "not-a-timestamp",
        [1234567890],
        {"ts": 1234567890},
        float("nan"),
        float("inf"),
        float("-inf"),
    ],
)
def test_token_with_invalid_exp_type_is_rejected(invalid_exp) -> None:
    settings = get_settings()
    now_ts = int(time.time())
    token = jwt.encode(
        {"sub": "42", "exp": invalid_exp, "iat": now_ts, "type": "access"},
        settings.secret_key,
        algorithm=settings.jwt_algorithm,
    )
    with pytest.raises(InvalidTokenError):
        decode_access_token(token)


@pytest.mark.parametrize("bool_exp", [False, True])
def test_token_with_boolean_exp_is_rejected(bool_exp) -> None:
    settings = get_settings()
    now_ts = int(time.time())
    token = jwt.encode(
        {"sub": "42", "exp": bool_exp, "iat": now_ts, "type": "access"},
        settings.secret_key,
        algorithm=settings.jwt_algorithm,
    )
    with pytest.raises(TokenError):
        decode_access_token(token)


@pytest.mark.parametrize(
    "invalid_iat",
    [
        False,
        True,
        "not-a-timestamp",
        [1234567890],
        {"ts": 1234567890},
        float("nan"),
        float("inf"),
        float("-inf"),
    ],
)
def test_token_with_invalid_iat_type_is_rejected(invalid_iat) -> None:
    settings = get_settings()
    now_ts = int(time.time())
    token = jwt.encode(
        {"sub": "42", "exp": now_ts + 300, "iat": invalid_iat, "type": "access"},
        settings.secret_key,
        algorithm=settings.jwt_algorithm,
    )
    with pytest.raises(InvalidTokenError):
        decode_access_token(token)


@pytest.mark.parametrize("missing_claim", ["exp", "sub", "iat"])
def test_token_with_missing_required_claim_is_rejected(missing_claim: str) -> None:
    settings = get_settings()
    now_ts = int(time.time())
    payload = {
        "sub": "42",
        "exp": now_ts + 300,
        "iat": now_ts,
        "type": "access",
    }
    payload.pop(missing_claim)
    token = jwt.encode(
        payload,
        settings.secret_key,
        algorithm=settings.jwt_algorithm,
    )
    with pytest.raises(InvalidTokenError):
        decode_access_token(token)


@pytest.mark.parametrize("invalid_sub", ["0", "-1", "-100", "", "   ", "abc"])
def test_token_with_malformed_sub_value_is_rejected_on_decode(invalid_sub: str) -> None:
    settings = get_settings()
    now_ts = int(time.time())
    token = jwt.encode(
        {"sub": invalid_sub, "exp": now_ts + 300, "iat": now_ts, "type": "access"},
        settings.secret_key,
        algorithm=settings.jwt_algorithm,
    )
    with pytest.raises(InvalidTokenError):
        decode_access_token(token)


def test_token_with_negative_timestamp_is_rejected() -> None:
    settings = get_settings()
    now_ts = int(time.time())
    token = jwt.encode(
        {"sub": "42", "exp": now_ts + 300, "iat": -1, "type": "access"},
        settings.secret_key,
        algorithm=settings.jwt_algorithm,
    )
    with pytest.raises(InvalidTokenError, match="Token timestamp claim is out of supported range"):
        decode_access_token(token)
