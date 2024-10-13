import logging

from flask import request, abort
from flask_jwt_extended import jwt_required, get_jwt

from common.password_utils import check_password
from common.response_wrapper import success_response, bad_request_response
from user import user
from user.service import get_user_by_email, blacklist_tokens, generate_tokens_from_refresh_token, generate_tokens

logger = logging.getLogger(__name__)

@user.post('/login')
def login():
    email = request.json.get('email', None)
    password = request.json.get('password', None)

    found_user = get_user_by_email(email)

    if not found_user:
        return abort(404, description=f"No user found with email {email}")

    if not check_password(found_user.password, password):
        return abort(401, description=f"Bad credentials")

    token = generate_tokens(found_user)
    return success_response({"access_token": token.access_token, "refresh_token": token.refresh_token})

@user.post('/logout')
@jwt_required()
def logout():
    refresh_token_provided = request.get_json()["refresh_token"]

    blacklist_tokens(get_jwt(), refresh_token_provided)

    return success_response({"message": "successfully logged out!"})

@user.post('/refresh-token')
def refresh_token():
    refresh_token_provided = request.get_json()["refresh_token"]

    if not refresh_token_provided:
        logger.info("no refresh token provided!")
        return bad_request_response({"description": "No refresh token provided!"})

    token = generate_tokens_from_refresh_token(refresh_token_provided)

    if not token:
        logger.info("token has been revoked or no user found with email provided!")
        return bad_request_response({"description": "Token has been revoked or no user found with email provided!"})

    return success_response({"access_token": token.access_token, "refresh_token": token.refresh_token})