import logging

from flask import request
from pydantic import ValidationError

from app.blueprints.traveler import traveler
from app.blueprints.traveler.model import CreateTravelerRequest, UpdateTravelerRequest, ConfirmTravelerSignupRequest, \
    TravelerSignupConfirmationNotFoundException
from app.blueprints.traveler.service import create_traveler, get_traveler_by_id, update_traveler, \
    handle_signup_confirmation
from app.exceptions import ElementAlreadyExistsException, ElementNotFoundException
from app.response_wrapper import bad_request_response, conflict_response, success_response, not_found_response, \
    error_response, no_content_response

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

@traveler.put('/<traveler_id>')
def update(traveler_id):
    try:
        logger.debug("parsing request body to traveler..")
        traveler_data = UpdateTravelerRequest(**request.json)

        update_traveler(traveler_id, traveler_data)
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
