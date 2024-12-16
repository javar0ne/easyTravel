from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, model_validator, ValidationError
from typing_extensions import Self

from app.encoders import PyObjectId
from app.models import Paginated
from app.role import Role
from app.utils import is_valid_enum_name

COLLECTION_NAME = "users"

class WrongPasswordException(Exception):
    def __init__(self, email):
        super().__init__(f"Wrong password provided for user with email {email}")

class ForgotPasswordTokenAlreadyUsed(Exception):
    def __init__(self):
        super().__init__("forgot password token already used!")

class RefreshTokenRevoked(Exception):
    def __init__(self):
        super().__init__("Refresh token revoked!")

class ForgotPasswordTokenStatus(Enum):
    CREATED = "created"
    USED = "used"

class SearchUserRequest(BaseModel):
    email: Optional[str] = None
    role: Optional[str] = None

    @model_validator(mode='before')
    def validate_before(self) -> Self:
        if self["role"] and not is_valid_enum_name(Role, self["role"]):
            raise ValidationError(f"{self['role']} is not a valid Role!")

        return self

    @model_validator(mode='after')
    def validate_after(self) -> Self:
        if not self.role and not self.email:
            raise ValidationError("At least one filter should be provided!")

        return self

class SearchUserResponse(BaseModel):
    id: str
    email: Optional[str] = None

class UserEmailResponse(BaseModel):
    id: str
    email: Optional[str] = None

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class LogoutRequest(BaseModel):
    refresh_token: str

class ResetPasswordRequest(BaseModel):
    token: str
    password: str

class ForgotPasswordRequest(BaseModel):
    email: str

class LoginRequest(BaseModel):
    email: str
    password: str

class User(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    email: str
    password: str
    roles: list[str]
    last_password_update: datetime

class Token(BaseModel):
    access_token: str
    refresh_token: str