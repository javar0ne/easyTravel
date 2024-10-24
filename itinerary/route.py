import logging

from flask import request
from openai import APIStatusError
from pydantic import ValidationError

from common.response_wrapper import success_response, bad_gateway_response, error_response, bad_request_response
from itinerary import itinerary
from itinerary.model import ItineraryRequest
from itinerary.service import get_city_description, generate_itinerary_request, get_itinerary_request_by_id

logger = logging.getLogger(__name__)

@itinerary.get('/<city_name>')
def get(city_name):
    try:
        city_description = get_city_description(city_name)

        return success_response(city_description.model_dump())
    except APIStatusError as err:
        logger.error(err)
        return bad_gateway_response()

@itinerary.post('/itinerary-request')
def gen_itinerary():
    try:
        logger.debug("parsing request body..")
        itinerary_request = ItineraryRequest(**request.json)
        request_id = generate_itinerary_request(itinerary_request)
        return success_response({"request_id": str(request_id)})
    except ValidationError as err:
        logger.error("validation error while parsing traveler request", err)
        return bad_request_response(err.errors())
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