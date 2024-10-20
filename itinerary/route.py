import logging

from openai import APIStatusError

from common.response_wrapper import success_response, bad_gateway_response
from itinerary import itinerary
from itinerary.service import get_city_description

logger = logging.getLogger(__name__)

@itinerary.get('/<city_name>')
def get(city_name):
    try:
        city_description = get_city_description(city_name)

        return success_response(city_description.model_dump())
    except APIStatusError as err:
        logger.error(err)
        return bad_gateway_response()
