import logging

from flask import request
from pydantic import ValidationError

from app.blueprints.admin import admin
from app.blueprints.admin.model import ItineraryActivationRequest
from app.blueprints.admin.service import handle_itinerary_activation
from app.response_wrapper import bad_request_response, no_content_response

logger = logging.getLogger(__name__)

@admin.post('/itinerary-activation')
def itinerary_activation():
    try:
        handle_itinerary_activation(ItineraryActivationRequest(**request.json))

        return no_content_response()
    except ValidationError as err:
        logger.error("validation error while parsing itinerary activation request")
        return bad_request_response(err.errors())