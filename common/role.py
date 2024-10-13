from enum import Enum
from functools import wraps
from flask_jwt_extended import jwt_required, get_jwt

from common.response_wrapper import forbidden_response

class Role(Enum):
    TRAVELER = "traveler"
    ORGANIZATION = "organization"
    ADMIN = "admin"

def role_required(required_role):
    def decorator(fn):
        @wraps(fn)
        @jwt_required()
        def wrapper(*args, **kwargs):
            claims = get_jwt()
            if required_role not in claims["roles"]:
                return forbidden_response()
            return fn(*args, **kwargs)
        return wrapper
    return decorator