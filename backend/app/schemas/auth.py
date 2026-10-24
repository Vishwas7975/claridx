"""Pydantic schemas for authentication and user profile endpoints."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.user import UserRole


class LoginRequest(BaseModel):
    """Credentials payload for user authentication.

    Supports 'email' directly or 'username' as an alias for OAuth2 client compatibility.
    """

    email: str = Field(..., description="User's email address")
    password: str = Field(..., min_length=1, description="User's plaintext password")

    model_config = ConfigDict(extra="ignore")

    @model_validator(mode="before")
    @classmethod
    def resolve_email_or_username(cls, data: Any) -> Any:
        if isinstance(data, dict) and "email" not in data and "username" in data:
            data = {**data, "email": data["username"]}
        return data


class TokenResponse(BaseModel):
    """Bearer access token response schema."""

    access_token: str = Field(..., description="Signed JWT access token")
    token_type: str = Field(default="bearer", description="Token type, always 'bearer'")

    model_config = ConfigDict(extra="ignore")


class UserProfileResponse(BaseModel):
    """Safe authenticated user profile schema omitting sensitive credentials."""

    id: int
    email: str
    full_name: str
    role: UserRole
    is_active: bool
    last_login_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True, extra="ignore")


class RegisterRequest(BaseModel):
    """Payload for public user self-registration."""

    email: str = Field(..., description="User's email address")
    full_name: str = Field(..., min_length=1, max_length=150, description="User's full name")
    password: str = Field(..., min_length=8, description="User plaintext password (min 8 chars)")
    confirm_password: str = Field(..., min_length=8, description="Confirmation of password")

    model_config = ConfigDict(extra="ignore")

    @model_validator(mode="after")
    def validate_password_match(self) -> "RegisterRequest":
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match")
        self.email = self.email.strip().lower()
        if "@" not in self.email or "." not in self.email.split("@")[-1]:
            raise ValueError("Invalid email address format")
        self.full_name = self.full_name.strip()
        if not self.full_name:
            raise ValueError("Full name cannot be empty")
        return self
