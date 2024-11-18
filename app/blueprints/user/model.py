from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from app.encoders import PyObjectId

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