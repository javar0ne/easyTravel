import logging

from flask import request
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity
from pydantic import ValidationError

from app.blueprints.user import user
from app.blueprints.user.model import ForgotPasswordRequest, ResetPasswordRequest, LoginRequest, WrongPasswordException, \
    LogoutRequest, \
    RefreshTokenRequest, RefreshTokenRevoked, SearchUserRequest
from app.blueprints.user.service import handle_login, handle_logout, \
    handle_refresh_token, handle_forgot_password, handle_reset_password, handle_search_user
from app.exceptions import ElementNotFoundException
from app.response_wrapper import success_response, bad_request_response, error_response, no_content_response, \
    not_found_response, unauthorized_response
from app.role import Role

logger = logging.getLogger(__name__)

@user.post('/login')
def login():
    try:
        login_req = LoginRequest(**request.json)
        token = handle_login(login_req)

        return success_response(token.model_dump())
    except ValidationError as err:
        logger.error("validation error while parsing login request")
        return bad_request_response(err.errors())
    except ElementNotFoundException as err:
        logger.warning(str(err))
        return not_found_response(err.message)
    except WrongPasswordException as err:
        logger.info(str(err))
        return unauthorized_response()
    except Exception as err:
        logger.error(str(err))
        return error_response()


@user.post('/logout')
@jwt_required()
def logout():
    try:
        logout_req = LogoutRequest(**request.json)
        handle_logout(get_jwt(), logout_req)

        return success_response({"message": "successfully logged out!"})
    except ValidationError as err:
        logger.error("validation error while parsing login request")
        return bad_request_response(err.errors())
    except Exception as err:
        logger.error(str(err))
        return error_response()

@user.post('/refresh-token')
@jwt_required(refresh=True)
def refresh_token():
    try:
        token = handle_refresh_token(get_jwt())
        return success_response(token.model_dump())
    except ValidationError as err:
        logger.error("validation error while parsing login request")
        return bad_request_response(err.errors())
    except RefreshTokenRevoked as err:
        logger.warning(str(err))
        return bad_request_response(str(err))
    except Exception as err:
        logger.error(str(err))
        return error_response()

@user.post('/forgot-password')
def forgot_password():
    try:
        forgot_password_req = ForgotPasswordRequest(**request.json)
        handle_forgot_password(forgot_password_req)

        return no_content_response()
    except ValidationError as err:
        logger.error("validation error while parsing forgot password request", err)
        return bad_request_response(err.errors())
    except Exception as err:
        logger.error(str(err))
        return error_response()

@user.post('/reset-password')
def reset_password():
    try:
        reset_password_req = ResetPasswordRequest(**request.json)
        token = handle_reset_password(reset_password_req)

        return success_response(token.model_dump())
    except ValidationError as err:
        logger.error("validation error while parsing reset password request", err)
        return bad_request_response(err.errors())
    except ElementNotFoundException as err:
        logger.warning(str(err))
        return not_found_response(err.message)
    except Exception as err:
        logger.error(str(err))
        return error_response()


@user.get('/dashboard')
@jwt_required()
def dashboard():
    roles = get_jwt()["roles"]

    if Role.ADMIN.name in roles:
        return success_response("/admin/dashboard")
    elif Role.ORGANIZATION.name in roles:
        return success_response("/organization/dashboard")
    elif Role.TRAVELER.name in roles:
        return success_response("/traveler/dashboard")
    else:
        logger.warning(f"no dashboard url found for user {get_jwt_identity()}")
        return not_found_response(f"no dashboard url found for user {get_jwt_identity()}")

@user.post('/search')
@jwt_required()
def search_user():
    try:
        search = SearchUserRequest(**request.json)
        users = handle_search_user(get_jwt_identity(), search)

        return success_response(users)
    except ValidationError as err:
        logger.error("validation error while parsing search user request", err)
        return bad_request_response(err.errors(include_context=False))
    except Exception as err:
        logger.error(str(err))
        return error_response()
