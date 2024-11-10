import logging

from flask import request
from pydantic import ValidationError

from admin import admin
from admin.model import ItineraryActivationRequest
from admin.service import handle_itinerary_activation
from common.response_wrapper import bad_request_response, no_content_response

logger = logging.getLogger(__name__)

@admin.post('/itinerary-activation')
def itinerary_activation():
    try:
        handle_itinerary_activation(ItineraryActivationRequest(**request.json))

        return no_content_response()
    except ValidationError as err:
        logger.error("validation error while parsing itinerary activation request")
        return bad_request_response(err.errors())