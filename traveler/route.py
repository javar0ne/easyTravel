import logging

from flask import request
from pydantic import ValidationError

from common.exception import ElementAlreadyExistsException, ElementNotFoundException
from common.response_wrapper import bad_request_response, conflict_response, success_response, not_found_response, \
    error_response, no_content_response
from traveler import traveler
from traveler.model import TravelerCreateModel, TravelerUpdateModel, TravelerModel
from traveler.service import create_traveler, get_traveler_by_id, update_traveler

logger = logging.getLogger(__name__)

@traveler.get('/<traveler_id>')
def get(traveler_id):
    try:
        traveler = get_traveler_by_id(traveler_id)
        return TravelerModel(**traveler).model_dump(), 200
    except ElementNotFoundException as err:
        logger.warning(str(err))
        return not_found_response(err.message)
    except Exception as err:
        logger.error(str(err))
        return error_response()

@traveler.post('/')
def create():
    try:
        logger.debug("parsing request body to traveler..")
        traveler_data = TravelerCreateModel(**request.json)

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
        traveler_data = TravelerUpdateModel(**request.json)

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


