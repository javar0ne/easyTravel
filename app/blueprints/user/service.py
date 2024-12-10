import logging
import secrets
from datetime import datetime, timezone, timedelta
from typing import Optional

from bson import ObjectId
from flask import current_app
from flask_jwt_extended import decode_token, create_access_token, create_refresh_token
from werkzeug.security import generate_password_hash, check_password_hash

from app.blueprints.user.mail import send_forgot_password_mail
from app.blueprints.user.model import User, Token, ForgotPasswordRequest, ResetPasswordRequest, \
    LoginRequest, \
    WrongPasswordException, LogoutRequest, RefreshTokenRequest, RefreshTokenRevoked
from app.exceptions import ElementAlreadyExistsException, ElementNotFoundException
from app.extensions import mongo, redis_auth
from app.models import Collections
from app.role import Role

logger = logging.getLogger(__name__)

def exists_admin():
    return mongo.count_documents(Collections.USERS, {"roles": Role.ADMIN.name}) > 0

def exists_by_email(email: str):
    return mongo.count_documents(Collections.USERS, {"email": email}) > 0

def get_user_by_email(email: str) -> Optional[User]:
    stored_user = mongo.find_one(Collections.USERS, {'email': email})

    if not stored_user:
        return None

    return User(**stored_user)

def get_user_by_id(user_id: str) -> Optional[User]:
    stored_user = mongo.find_one(Collections.USERS, {'_id': ObjectId(user_id)})

    if not stored_user:
        return None

    return User(**stored_user)

def handle_login(login_req: LoginRequest) -> Token:
    user = get_user_by_email(login_req.email)
    if not user:
        raise ElementNotFoundException(f"no user found with email {login_req.email}")

    if not check_password_hash(user.password, login_req.password):
        raise WrongPasswordException(user.email)

    return generate_tokens(user)

def handle_logout(access_token: dict, logout_req: LogoutRequest):
    logger.info("blacklisting tokens for user %s..", access_token['sub'])
    blacklist_tokens(access_token, logout_req.refresh_token)
    logger.info("blacklisted tokens for user %s..", access_token['sub'])

def handle_refresh_token(refresh_token: dict) -> Token:
    return generate_tokens_from_refresh_token(refresh_token)

def create_user(email: str, password: str, roles: list[str]) -> Optional[ObjectId]:
    if exists_by_email(email):
        raise ElementAlreadyExistsException(f"user already exists with email: {email}")

    password = generate_password_hash(password)

    user = User(email=email, password=password, roles=roles, last_password_update=datetime.now(timezone.utc))

    return mongo.insert_one(Collections.USERS, user.model_dump(exclude={"id"})).inserted_id

def blacklist_token(jwt: dict):
    jti = jwt["jti"]

    expire_timestamp = datetime.fromtimestamp(jwt["exp"])
    current_timestamp = datetime.now()
    expire = expire_timestamp - current_timestamp

    redis_auth.get_client().set(jti, "", expire)

def blacklist_refresh_token(token: str):
    jwt = decode_token(token)
    blacklist_token(jwt)

def blacklist_tokens(access_token: dict, refresh_token: str):
    blacklist_token(access_token)
    blacklist_refresh_token(refresh_token)

def generate_tokens_from_refresh_token(refresh_token: dict) -> Optional[Token]:
    if is_token_not_valid(refresh_token.get("sub"), refresh_token.get("iat"), refresh_token.get("jti")):
        raise RefreshTokenRevoked()

    user = get_user_by_id(refresh_token.get('sub'))
    if not user:
        logger.info("no user found with id %s", refresh_token.get('sub'))
        return None

    return generate_tokens(user)

def generate_tokens(user: User) -> Token:
    logger.info("generating tokens for user %s..", user.id)

    new_access_token = create_access_token(identity=user.id, additional_claims={'roles': user.roles, "email": user.email})
    new_refresh_token = create_refresh_token(identity=user.id, additional_claims={'roles': user.roles, "email": user.email})

    logger.info("generated tokens for user %s!", user.id)

    return Token(access_token=new_access_token, refresh_token=new_refresh_token)


def generate_reset_url(token: str):
    return current_app.config["APP_HOST"] + "/user/reset-password/" + token

def handle_forgot_password(forgot_password_req: ForgotPasswordRequest):
    user = get_user_by_email(forgot_password_req.email)
    if not user:
        raise ElementNotFoundException(f"no user registered with email {forgot_password_req.email}")

    token = secrets.token_urlsafe(16)
    mongo.insert_one(
        Collections.RESET_TOKENS,
        {
            "user_id": user.id,
            "token": token,
            "expires_at": datetime.now(timezone.utc) + timedelta(minutes=15)
        }
    )
    reset_url = generate_reset_url(token)

    send_forgot_password_mail(forgot_password_req.email, reset_url)

def handle_reset_password(reset_password_req: ResetPasswordRequest) -> Token:
    reset_token = mongo.find_one(Collections.RESET_TOKENS, {"token": reset_password_req.token})

    if not reset_token:
        raise ElementNotFoundException(f"no reset token found with value {reset_password_req.token}")

    user_id = reset_token.get("user_id")

    logger.info("resetting user %s password..", user_id)

    mongo.update_one(
        Collections.USERS,
        {"_id": ObjectId(user_id)},
        {"$set":
            {
                "password": generate_password_hash(reset_password_req.password),
                "last_password_update": datetime.now(timezone.utc) - timedelta(seconds=1)
            }
        }
    )

    mongo.delete_one(Collections.USERS, {"_id": reset_token.get("_id")})

    logger.info("user %s password reset!", user_id)

    return generate_tokens(get_user_by_id(user_id))

def is_token_not_valid(user_id: str, iat: int, jti) -> bool:
    projected_user = mongo.find_one(Collections.USERS, {"_id": ObjectId(user_id)}, {"last_password_update": 1, "_id": 0})
    last_password_update = projected_user.get("last_password_update").replace(tzinfo=timezone.utc)
    issued_at = datetime.fromtimestamp(iat, timezone.utc)

    return issued_at < last_password_update or redis_auth.get_client().exists(jti)