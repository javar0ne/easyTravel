from enum import Enum
from functools import wraps

from flask_jwt_extended import jwt_required, get_jwt

from app.response_wrapper import forbidden_response


class Role(Enum):
    TRAVELER = "traveler"
    ORGANIZATION = "organization"
    ADMIN = "admin"

def roles_required(required_roles: list[str]):
    def decorator(fn):
        @wraps(fn)
        @jwt_required()
        def wrapper(*args, **kwargs):
            has_required_role = False
            claims = get_jwt()
            for required_role in required_roles:
                if required_role in claims["roles"]:
                    has_required_role = True

            if not has_required_role:
                return forbidden_response()

            return fn(*args, **kwargs)
        return wrapper
    return decorator