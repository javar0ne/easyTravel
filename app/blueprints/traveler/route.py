import logging

from flask import request
from flask_jwt_extended import get_jwt_identity
from pydantic import ValidationError

from app.blueprints.traveler import traveler
from app.blueprints.traveler.model import CreateTravelerRequest, UpdateTravelerRequest, ConfirmTravelerSignupRequest, \
    TravelerSignupConfirmationNotFoundException
from app.blueprints.traveler.service import create_traveler, get_traveler_by_id, update_traveler, \
    handle_signup_confirmation, get_traveler_by_user_id, get_full_traveler_by_id
from app.exceptions import ElementAlreadyExistsException, ElementNotFoundException
from app.response_wrapper import bad_request_response, conflict_response, success_response, not_found_response, \
    error_response, no_content_response
from app.role import roles_required, Role

logger = logging.getLogger(__name__)

@traveler.get('/<traveler_id>')
def get_traveler(traveler_id):
    try:
        traveler = get_traveler_by_id(traveler_id)
        return success_response(traveler.model_dump())
    except ElementNotFoundException as err:
        logger.warning(str(err))
        return not_found_response(err.message)
    except Exception as err:
        logger.error(str(err))
        return error_response()

@traveler.get('/full')
@roles_required([Role.TRAVELER.name])
def get_full_traveler():
    try:
        traveler = get_full_traveler_by_id(get_jwt_identity())
        return success_response(traveler.model_dump())
    except ElementNotFoundException as err:
        logger.warning(str(err))
        return not_found_response(err.message)
    except Exception as err:
        logger.error(str(err))
        return error_response()

@traveler.get('')
@roles_required([Role.TRAVELER.name])
def get_logged_traveler():
    try:
        traveler = get_traveler_by_user_id(get_jwt_identity())
        return success_response(traveler.model_dump())
    except ElementNotFoundException as err:
        logger.warning(str(err))
        return not_found_response(err.message)
    except Exception as err:
        logger.error(str(err))
        return error_response()

@traveler.post('')
def create():
    try:
        logger.debug("parsing request body to traveler..")
        traveler_data = CreateTravelerRequest(**request.json)

        inserted_id = create_traveler(traveler_data)
        return success_response({"id": inserted_id})
    except ValidationError as err:
        logger.error("validation error while parsing traveler request", err)
        return bad_request_response(err.errors())
    except ElementAlreadyExistsException as err:
        logger.error(err.message, err)
        return conflict_response(err.message)
    except Exception as err:
        logger.error(str(err))
        return error_response()

@traveler.put('')
@roles_required([Role.TRAVELER.name])
def update():
    try:
        logger.debug("parsing request body to traveler..")
        traveler_data = UpdateTravelerRequest(**request.json)

        update_traveler(get_jwt_identity(), traveler_data)
        return no_content_response()
    except ValidationError as err:
        logger.error("validation error while parsing traveler request", err)
        return bad_request_response(err.errors())
    except ElementNotFoundException as err:
        logger.warning(str(err))
        return not_found_response(err.message)
    except Exception as err:
        logger.error(str(err))
        return error_response()

@traveler.post("/confirm-signup")
def confirm_signup():
    try:
        confirm_signup_request = ConfirmTravelerSignupRequest(**request.json)
        handle_signup_confirmation(confirm_signup_request)

        return no_content_response()
    except ValidationError as err:
        logger.error("validation error while parsing traveler request", err)
        return bad_request_response(err.errors())
    except TravelerSignupConfirmationNotFoundException as err:
        logger.warning(str(err))
        return not_found_response(err.message)
    except Exception as err:
        logger.error(str(err))
        return error_response()