import logging

from flask import request
from flask_jwt_extended import get_jwt_identity
from pydantic import ValidationError

from app.blueprints.event import event
from app.blueprints.event.model import UpdateEventRequest, CreateEventRequest
from app.blueprints.event.service import create_event, update_event, delete_event, search_events, \
    get_event_by_user_and_id, get_upcoming_events, get_other_events, get_past_events, get_events_stats, get_event_by_id
from app.exceptions import ElementNotFoundException, OrganizationNotActiveException
from app.models import Paginated
from app.response_wrapper import bad_request_response, error_response, success_response, no_content_response, \
    not_found_response, forbidden_response
from app.role import roles_required, Role

logger = logging.getLogger(__name__)

@event.get('/<event_id>')
@roles_required([Role.ORGANIZATION.name])
def get(event_id):
    try:
        event = get_event_by_user_and_id(get_jwt_identity(), event_id)
        return success_response(event.model_dump())
    except ElementNotFoundException as err:
        logger.warning(str(err))
        return not_found_response(err.message)
    except OrganizationNotActiveException as err:
        return forbidden_response(err.message)
    except Exception as err:
        logger.error(str(err))
        return error_response()

@event.get('/itinerary/<event_id>')
@roles_required([Role.TRAVELER.name])
def get_for_itinerary(event_id):
    try:
        event = get_event_by_id(event_id)
        return success_response(event.model_dump())
    except ElementNotFoundException as err:
        logger.warning(str(err))
        return not_found_response(err.message)
    except OrganizationNotActiveException as err:
        return forbidden_response(err.message)
    except Exception as err:
        logger.error(str(err))
        return error_response()

@event.post('')
@roles_required([Role.ORGANIZATION.name])
def create():
    try:
        event = CreateEventRequest(**request.json)
        inserted_id = create_event(get_jwt_identity(), event)

        return success_response({"id": inserted_id})
    except ValidationError as err:
        logger.error("validation error while parsing event request", err)
        return bad_request_response(err.errors())
    except OrganizationNotActiveException as err:
        return forbidden_response()
    except Exception as err:
        logger.error(str(err))
        return error_response()

@event.put('/<event_id>')
@roles_required([Role.ORGANIZATION.name])
def update(event_id):
    try:
        update_event_req = UpdateEventRequest(**request.json)
        updated_id = update_event(get_jwt_identity(), event_id, update_event_req)

        return success_response({"id": updated_id})
    except ValidationError as err:
        logger.error("validation error while parsing event update request", err)
        return bad_request_response(err.errors())
    except OrganizationNotActiveException as err:
        return forbidden_response(err.message)
    except ElementNotFoundException as err:
        logger.warning(str(err))
        return not_found_response(err.message)
    except Exception as err:
        logger.error(str(err))
        return error_response()

@event.delete('/<event_id>')
@roles_required([Role.ORGANIZATION.name])
def delete(event_id):
    try:
        delete_event(get_jwt_identity(), event_id)

        return no_content_response()
    except ElementNotFoundException as err:
        logger.warning(str(err))
        return not_found_response(err.message)
    except OrganizationNotActiveException as err:
        return forbidden_response(err.message)
    except Exception as err:
        logger.error(str(err))
        return error_response()

@event.post('/search')
@roles_required([Role.ORGANIZATION.name])
def search():
    try:
        paginated = Paginated(**request.json)
        events = search_events(get_jwt_identity(), paginated)

        return success_response(events.model_dump())
    except ValidationError as err:
        logger.error("validation error while parsing search events request", err)
        return bad_request_response(err.errors())
    except OrganizationNotActiveException as err:
        return forbidden_response(err.message)
    except Exception as err:
        logger.error(str(err))
        return error_response()

@event.post('/upcoming')
@roles_required([Role.ORGANIZATION.name])
def upcoming():
    try:
        paginated = Paginated(**request.json)
        events = get_upcoming_events(get_jwt_identity(), paginated)

        return success_response(events.model_dump())
    except ValidationError as err:
        logger.error("validation error while parsing upcoming events request", err)
        return bad_request_response(err.errors())
    except OrganizationNotActiveException as err:
        return forbidden_response(err.message)
    except Exception as err:
        logger.error(str(err))
        return error_response()

@event.get('/other')
@roles_required([Role.ORGANIZATION.name])
def other():
    try:
        events = get_other_events(get_jwt_identity())
        return success_response(events)
    except ValidationError as err:
        logger.error("validation error while parsing upcoming events request", err)
        return bad_request_response(err.errors())
    except OrganizationNotActiveException as err:
        return forbidden_response(err.message)
    except Exception as err:
        logger.error(str(err))
        return error_response()

@event.get('/past')
@roles_required([Role.ORGANIZATION.name])
def past():
    try:
        events = get_past_events(get_jwt_identity())
        return success_response(events)
    except OrganizationNotActiveException as err:
        return forbidden_response(err.message)
    except Exception as err:
        logger.error(str(err))
        return error_response()

@event.get("/stats")
@roles_required([Role.ORGANIZATION.name])
def stats():
    try:
        event_stats = get_events_stats(get_jwt_identity())
        return success_response(event_stats.model_dump())
    except OrganizationNotActiveException as err:
        return forbidden_response(err.message)
    except Exception as err:
        logger.error(str(err))
        return error_response()
