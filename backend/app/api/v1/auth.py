"""Authentication endpoints: login and authenticated user profile.

POST /login accepts both application/json and application/x-www-form-urlencoded
so that OAuth2-compatible clients (including Swagger UI) can authenticate using
the standard password grant form fields (username, password).
"""

from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import ValidationError
from sqlalchemy import select
from starlette.datastructures import Headers

from app.api.deps import CurrentUserDep, DbDep
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.schemas.auth import LoginRequest, TokenResponse, UserProfileResponse

router = APIRouter()

# Fixed dummy Argon2id hash used to perform constant-time verification when an email is not found.
_DUMMY_HASH = hash_password("claridx-timing-defense-secret-hash")

# OpenAPI extra for /login: document both JSON and form-encoded request bodies.
# Schemas are inlined (not $ref) because the endpoint takes Request directly,
# so FastAPI does not generate a LoginRequest component automatically.
_LOGIN_OPENAPI_EXTRA: dict = {
    "requestBody": {
        "required": True,
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                    "title": "LoginRequest",
                    "description": (
                        "Credentials payload for user authentication."
                        " Supports 'email' or 'username' (OAuth2 alias)."
                    ),
                    "required": ["email", "password"],
                    "properties": {
                        "email": {
                            "type": "string",
                            "title": "Email",
                            "description": "User's email address",
                        },
                        "password": {
                            "type": "string",
                            "title": "Password",
                            "minLength": 1,
                            "description": "User's plaintext password",
                        },
                    },
                }
            },
            "application/x-www-form-urlencoded": {
                "schema": {
                    "type": "object",
                    "title": "OAuth2LoginForm",
                    "description": "Standard OAuth2 Password flow form fields.",
                    "required": ["username", "password"],
                    "properties": {
                        "username": {
                            "type": "string",
                            "title": "Username",
                            "description": "User's email address (OAuth2 username field)",
                        },
                        "password": {
                            "type": "string",
                            "title": "Password",
                            "description": "User's plaintext password",
                        },
                    },
                }
            },
        },
    }
}


def _verify_credentials(email: str, password: str, db: DbDep) -> TokenResponse:  # type: ignore[valid-type]
    """Shared credential-authentication logic used by both JSON and form-encoded login paths.

    Updates last_login_at only on success. Raises HTTPException for all failure modes.
    Never logs passwords, hashes, or tokens.
    """
    email_clean = email.strip().lower()
    user = db.scalars(select(User).where(User.email == email_clean)).first()

    if user is None:
        # Prevent user enumeration: run a real Argon2id verification so the response
        # time is indistinguishable from a wrong-password failure for a real account.
        verify_password(password, _DUMMY_HASH)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user account",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Update last_login_at only after all checks pass.
    user.last_login_at = datetime.now(UTC)
    db.commit()
    db.refresh(user)

    access_token = create_access_token(subject=user.id)
    return TokenResponse(access_token=access_token, token_type="bearer")


@router.post(
    "/login",
    response_model=TokenResponse,
    openapi_extra=_LOGIN_OPENAPI_EXTRA,
)
async def login(
    request: Request,
    db: DbDep,
) -> TokenResponse:
    """Authenticate with email/password, returning an OAuth2 bearer access token.

    Accepts **application/json** (``{"email": ..., "password": ...}``) or the standard
    OAuth2 **application/x-www-form-urlencoded** body (``username=...&password=...``).
    Both formats share the same authentication logic, failure responses, and
    ``last_login_at`` behaviour.
    """
    ct_raw = request.headers.get("content-type")
    if not ct_raw:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=(
                "Content-Type header is required. "
                "Use 'application/json' or 'application/x-www-form-urlencoded'."
            ),
        )

    # Normalise to lowercase base media type (strips "; charset=…" and casing per RFC 2045).
    ct_base = ct_raw.split(";")[0].strip().lower()

    if ct_base == "application/x-www-form-urlencoded":
        # Ensure Starlette's case-sensitive form parser receives the normalized lower-case
        # content-type in the ASGI scope, preserving any boundary or charset parameters.
        if not ct_raw.startswith(ct_base):
            parts = ct_raw.split(";", 1)
            params = (";" + parts[1]) if len(parts) > 1 else ""
            normalized_ct = (ct_base + params).encode("latin-1")
            request.scope["headers"] = [
                (b"content-type", normalized_ct) if k.lower() == b"content-type" else (k, v)
                for k, v in request.scope.get("headers", [])
            ]
            request._headers = Headers(scope=request.scope)

        form = await request.form()
        # OAuth2 Password flow sends 'username'; accept 'email' as a synonym.
        email = str(form.get("username") or form.get("email") or "").strip()
        password = str(form.get("password") or "").strip()
        if not email or not password:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="username (email) and password fields are required",
            )
    elif ct_base == "application/json":
        # JSON path (explicit application/json).
        try:
            body = await request.json()
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Request body must be valid JSON",
            ) from exc
        try:
            credentials = LoginRequest.model_validate(body)
        except ValidationError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=exc.errors(include_url=False),
            ) from exc
        email = credentials.email
        password = credentials.password
    else:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=(
                f"Unsupported Content-Type '{ct_base}'. "
                "Use 'application/json' or 'application/x-www-form-urlencoded'."
            ),
        )

    return _verify_credentials(email, password, db)


@router.get("/me", response_model=UserProfileResponse)
def read_current_user(
    current_user: CurrentUserDep,
) -> User:
    """Retrieve the safe profile of the currently authenticated active user."""
    return current_user
