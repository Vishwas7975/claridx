"""Security primitives: Argon2id password hashing and signed JWT access tokens."""

import math
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import jwt
from pwdlib import PasswordHash
from pwdlib.exceptions import PwdlibError

from app.core.config import get_settings

password_hash = PasswordHash.recommended()
ALLOWED_JWT_ALGORITHMS: frozenset[str] = frozenset({"HS256"})


class TokenError(ValueError):
    """Base exception for invalid, expired, or malformed authentication tokens."""


class ExpiredTokenError(TokenError):
    """Raised when an access token has expired."""


class InvalidTokenError(TokenError):
    """Raised when an access token is malformed, untrusted, or has an invalid signature."""


@dataclass(frozen=True)
class TokenPayload:
    """Explicit contract for decoded JWT access token claims."""

    sub: str
    exp: datetime
    token_type: str
    iat: datetime | None = None

    @property
    def user_id(self) -> int:
        """Parse the integer user ID from the subject claim."""
        try:
            uid = int(self.sub)
            if uid <= 0:
                raise ValueError("User ID must be a positive integer.")
            return uid
        except (ValueError, TypeError) as exc:
            raise InvalidTokenError(
                f"Token subject is not a valid integer user ID: {self.sub!r}"
            ) from exc


def hash_password(password: str) -> str:
    """Hash a plaintext password using Argon2id."""
    return password_hash.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against an Argon2id hash.

    Returns False if verification fails or if the stored hash is malformed/unsupported.
    """
    try:
        return password_hash.verify(plain_password, hashed_password)
    except (PwdlibError, ValueError):
        return False


def _validate_algorithm(algorithm: str) -> str:
    if algorithm not in ALLOWED_JWT_ALGORITHMS:
        raise InvalidTokenError("Configured JWT algorithm is not allowed.")
    return algorithm


def create_access_token(
    subject: str | int,
    expires_delta: timedelta | None = None,
) -> str:
    """Generate a signed JWT access token for a given user ID subject."""
    if isinstance(subject, int):
        if subject <= 0:
            raise ValueError("Token subject must be a positive integer user ID.")
        sub_str = str(subject)
    elif isinstance(subject, str):
        sub_str = subject.strip()
        if not sub_str or not sub_str.isdigit() or int(sub_str) <= 0:
            raise ValueError("Token subject must be a positive integer user ID string.")
    else:
        raise ValueError("Token subject must be an integer or integer string.")

    settings = get_settings()
    algorithm = _validate_algorithm(settings.jwt_algorithm)
    now = datetime.now(UTC)
    if expires_delta is not None:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.access_token_expire_minutes)

    payload = {
        "sub": sub_str,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
        "type": "access",
    }
    return jwt.encode(
        payload,
        settings.secret_key,
        algorithm=algorithm,
    )


def decode_access_token(token: str) -> TokenPayload:
    """Decode and validate a signed JWT access token.

    Validates signature, algorithm, expiration, token type, and subject.
    Raises ExpiredTokenError when expired, or InvalidTokenError when malformed/invalid.
    """
    settings = get_settings()
    algorithm = _validate_algorithm(settings.jwt_algorithm)
    try:
        raw_payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[algorithm],
            options={"require": ["exp", "sub", "iat"]},
        )
    except jwt.ExpiredSignatureError as exc:
        raise ExpiredTokenError("Token has expired.") from exc
    except jwt.PyJWTError as exc:
        raise InvalidTokenError(f"Invalid token: {exc}") from exc

    if "type" not in raw_payload or raw_payload["type"] != "access":
        raise InvalidTokenError("Invalid or missing token type claim.")

    sub = raw_payload.get("sub")
    if not isinstance(sub, str) or not sub.strip():
        raise InvalidTokenError("Token subject must be a non-empty string.")

    exp_ts = raw_payload.get("exp")
    iat_ts = raw_payload.get("iat")

    if (
        isinstance(exp_ts, bool)
        or not isinstance(exp_ts, (int, float))
        or math.isnan(exp_ts)
        or math.isinf(exp_ts)
    ):
        raise InvalidTokenError("Token expiration claim must be a valid numeric timestamp.")
    if (
        isinstance(iat_ts, bool)
        or not isinstance(iat_ts, (int, float))
        or math.isnan(iat_ts)
        or math.isinf(iat_ts)
    ):
        raise InvalidTokenError("Token issued-at claim must be a valid numeric timestamp.")

    if exp_ts < 0 or iat_ts < 0:
        raise InvalidTokenError("Token timestamp claim is out of supported range.")

    try:
        exp_dt = datetime.fromtimestamp(exp_ts, tz=UTC)
        iat_dt = datetime.fromtimestamp(iat_ts, tz=UTC) if iat_ts is not None else None
    except (ValueError, OSError, OverflowError) as exc:
        raise InvalidTokenError("Token timestamp claim is out of supported range.") from exc

    payload = TokenPayload(
        sub=sub,
        exp=exp_dt,
        token_type=raw_payload["type"],
        iat=iat_dt,
    )
    # Validate that sub parses as user_id
    _ = payload.user_id
    return payload
