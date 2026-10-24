from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.core.security import TokenError, decode_access_token
from app.models.user import User, UserRole
from app.services.diabetes_registry import DiabetesModelRegistry
from app.services.model_registry import ModelRegistry

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{get_settings().api_v1_prefix}/auth/login",
    auto_error=False,
)

DbDep = Annotated[Session, Depends(get_db)]
TokenDep = Annotated[str | None, Depends(oauth2_scheme)]


def get_current_user(
    token: TokenDep,
    db: DbDep,
) -> User:
    """Decode signed access token and retrieve authoritative user record from the database."""
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        payload = decode_access_token(token)
    except TokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    user = db.get(User, payload.user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Ensure the authenticated user account is active."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user account",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return current_user


CurrentUserDep = Annotated[User, Depends(get_current_active_user)]


def require_roles(*allowed_roles: UserRole):
    """Factory creating an endpoint dependency that ensures the active user has an allowed role.

    Always inspects the database-loaded User record (from get_current_active_user).
    Raises HTTP 403 Forbidden if the user's role is not in allowed_roles.
    """
    allowed_set = set(allowed_roles)

    def role_checker(
        current_user: Annotated[User, Depends(get_current_active_user)],
    ) -> User:
        if current_user.role not in allowed_set:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions",
            )
        return current_user

    return role_checker


PredictionUserDep = Annotated[
    User,
    Depends(require_roles(UserRole.ADMIN, UserRole.DOCTOR, UserRole.PATIENT)),
]


def get_registry(request: Request) -> ModelRegistry:
    registry = getattr(request.app.state, "registry", None)
    if registry is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Prediction models are not loaded.",
        )
    return registry


RegistryDep = Annotated[ModelRegistry, Depends(get_registry)]


def get_diabetes_registry(request: Request) -> DiabetesModelRegistry:
    registry = getattr(request.app.state, "diabetes_registry", None)
    if registry is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Diabetes prediction models are not loaded.",
        )
    return registry


DiabetesRegistryDep = Annotated[DiabetesModelRegistry, Depends(get_diabetes_registry)]
