import logging
from flask import request
from flask_jwt_extended import get_jwt_identity

from pydantic import ValidationError

from common.exceptions import ElementNotFoundException
from common.model import Paginated
from common.response_wrapper import bad_request_response, error_response, success_response, no_content_response, \
    not_found_response
from common.role import roles_required, Role
from event import event
from event.model import Event, UpdateEventRequest
from event.service import create_event, update_event, get_event_by_id, delete_event

logger = logging.getLogger(__name__)

@event.get('/<event_id>')
def get(event_id):
    try:
        event = get_event_by_id(event_id)
        return success_response(event.model_dump())
    except ElementNotFoundException as err:
        logger.warning(str(err))
        return not_found_response(err.message)
    except Exception as err:
        logger.error(str(err))
        return error_response()

@event.post('/')
@roles_required([Role.ORGANIZATION.name])
def create():
    try:
        event = Event(**request.json)
        inserted_id = create_event(get_jwt_identity(), event)

        return success_response({"id": inserted_id})
    except ValidationError as err:
        logger.error("validation error while parsing event request", err)
        return bad_request_response(err.errors())
    except Exception as err:
        logger.error(str(err))
        return error_response()

@event.put('/<event_id>')
def update(event_id):
    try:
        update_event_req = UpdateEventRequest(**request.json)
        update_event(event_id, update_event_req)

        return no_content_response()
    except ValidationError as err:
        logger.error("validation error while parsing itinerary request", err)
        return bad_request_response(err.errors())
    except ElementNotFoundException as err:
        logger.warning(str(err))
        return not_found_response(err.message)
    except Exception as err:
        logger.error(str(err))
        return error_response()

@event.delete('/<event_id>')
def delete(event_id):
    try:
        delete_event(event_id)

        return no_content_response()
    except ElementNotFoundException as err:
        logger.warning(str(err))
        return not_found_response(err.message)
    except Exception as err:
        logger.error(str(err))
        return error_response()

@event.get('')
@roles_required([Role.ORGANIZATION.name])
def search():
    try:
        paginated = Paginated(**request.json)
        events = search_events(get_jwt_identity(), paginated)

        return success_response(events.model_dump())
    except ValidationError as err:
        logger.error("validation error while parsing search events request", err)
        return bad_request_response(err.errors())
    except Exception as err:
        logger.error(str(err))
        return error_response()