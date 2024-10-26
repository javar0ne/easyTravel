import logging

from flask import request
from openai import APIStatusError
from pydantic import ValidationError

from common.exception import ElementNotFoundException
from common.response_wrapper import success_response, bad_gateway_response, error_response, bad_request_response, \
    no_content_response, not_found_response
from itinerary import itinerary
from itinerary.model import ItineraryRequest, Itinerary, ShareWithRequest, PublishReqeust, DuplicateRequest
from itinerary.service import get_city_description, generate_itinerary_request, get_itinerary_request_by_id, \
    get_itinerary_by_id, create_itinerary, share_with, publish, completed, duplicate

logger = logging.getLogger(__name__)

@itinerary.get('/<itinerary_id>')
def get_itinerary(itinerary_id):
    try:
        itinerary = get_itinerary_by_id(itinerary_id)
        return Itinerary(**itinerary)
    except Exception as err:
        logger.error(str(err))
        return error_response()

@itinerary.post('/create/<itinerary_request_id>')
def create(itinerary_request_id):
    try:
        inserted_id = create_itinerary(itinerary_request_id)
        return success_response({"id": inserted_id})
    except ValidationError as err:
        logger.error("validation error while parsing traveler request", err)
        return bad_request_response(err.errors())
    except Exception as err:
        logger.error(str(err))
        return error_response()

@itinerary.post('/share-with')
def share_itinerary_with():
    try:
        users = ShareWithRequest(**request.json)
        share_with(users)

        return no_content_response()
    except ElementNotFoundException as err:
        logger.warning(str(err))
        return not_found_response(err.message)
    except Exception as err:
        logger.error(str(err))
        return error_response()

@itinerary.post('/publish')
def publish_itinerary():
    try:
        publish(PublishReqeust(**request.json))

        return no_content_response()
    except ValidationError as err:
        logger.error("validation error while parsing publish itinerary reqeust", err)
        return bad_request_response(err.errors(include_context=False))
    except ElementNotFoundException as err:
        logger.warning(str(err))
        return not_found_response(err.message)
    except Exception as err:
        logger.error(str(err))
        return error_response()

@itinerary.post('/completed/<itinerary_id>')
def itinerary_completed(itinerary_id):
    try:
        completed(itinerary_id)

        return no_content_response()
    except ElementNotFoundException as err:
        logger.warning(str(err))
        return not_found_response(err.message)
    except Exception as err:
        logger.error(str(err))
        return error_response()

@itinerary.post('/duplicate')
def duplicate_itinerary():
    try:
        inserted_id = duplicate(DuplicateRequest(**request.json))

        return success_response({"id": inserted_id})
    except ElementNotFoundException as err:
        logger.warning(str(err))
        return not_found_response(err.message)
    except Exception as err:
        logger.error(str(err))
        return error_response()

@itinerary.get('/city-description/<city_name>')
def city_description(city_name):
    try:
        cd = get_city_description(city_name)
        return success_response(cd.model_dump())
    except APIStatusError as err:
        logger.error(str(err))
        return bad_gateway_response()
    except Exception as err:
        logger.error(str(err))
        return error_response()

@itinerary.post('/itinerary-request')
def gen_itinerary():
    try:
        logger.debug("parsing request body..")
        itinerary_request = ItineraryRequest(**request.json)
        request_id = generate_itinerary_request(itinerary_request)
        return success_response({"request_id": str(request_id)})
    except ValidationError as err:
        logger.error("validation error while parsing itinerary request", err)
        return bad_request_response(err.errors(include_context=False))
    except Exception as err:
        logger.error(str(err))
        return error_response()

@itinerary.get('/itinerary-request/<request_id>')
def get_itinerary_request(request_id):
    try:
        itinerary_request = get_itinerary_request_by_id(request_id)
        return success_response(itinerary_request.model_dump())
    except Exception as err:
        logger.error(str(err))
        return error_response()