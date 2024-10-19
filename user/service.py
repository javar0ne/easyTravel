import logging
from datetime import datetime
from typing import Optional

from bson import ObjectId

from flask_jwt_extended import decode_token, create_access_token, create_refresh_token

from common.exception import ElementAlreadyExistsException
from common.extensions import db, redis
from common.password_utils import hash_password
from user.model import COLLECTION_NAME, User, Token

logger = logging.getLogger(__name__)
collection = db[COLLECTION_NAME]

class NotFoundException(Exception):
    def __init__(self,msg):
        super().__init__(msg)

def get_user_by_email(email: str) -> Optional[User]:
    stored_user = collection.find_one({'email': email})

    if not stored_user:
        return None

    return User(**stored_user)

def create_user(email: str, password: str, roles: list[str]) -> Optional[ObjectId]:
    if get_user_by_email(email):
        raise ElementAlreadyExistsException(f"user already exists with email: {email}")

    password = hash_password(password)

    user = User(email=email, password=password, roles=roles)

    return collection.insert_one(user.to_dict()).inserted_id

def blacklist_token(jwt: dict):
    jti = jwt["jti"]

    expire_timestamp = datetime.fromtimestamp(jwt["exp"])
    current_timestamp = datetime.now()
    expire = expire_timestamp - current_timestamp

    redis.set(jti, "", expire)

def blacklist_refresh_token(token: str):
    jwt = decode_token(token)
    blacklist_token(jwt)

def blacklist_tokens(access_token: dict, refresh_token: str):
    blacklist_token(access_token)
    blacklist_refresh_token(refresh_token)

def generate_tokens_from_refresh_token(refresh_token: str) -> Optional[Token]:
    jwt = decode_token(refresh_token)

    if redis.exists(jwt['jti']):
        logging.info("refresh token has been revoked")
        return None

    user = get_user_by_email(jwt['email'])
    if not user:
        logger.info("no user found with email %s", jwt['email'])
        return None

    return generate_tokens(user)

def generate_tokens(user: User) -> Token:
    new_access_token = create_access_token(identity=user._id,
                                           additional_claims={'roles': user.roles, "email": user.email})
    new_refresh_token = create_refresh_token(identity=user._id,
                                             additional_claims={'roles': user.roles, "email": user.email})

    return Token(new_access_token, new_refresh_token)
