import logging
from datetime import datetime, timezone

from bson import ObjectId

from app.blueprints.event.model import Event, UpdateEventRequest, CreateEventRequest
from app.blueprints.organization.model import OrganizationStatus
from app.blueprints.organization.service import is_organization_active, \
    get_organization_by_user_id
from app.exceptions import ElementNotFoundException, OrganizationNotActiveException
from app.extensions import mongo
from app.models import Paginated, PaginatedResponse, Collections

logger = logging.getLogger(__name__)

def get_event_by_id(event_id: str) -> Event:
    logger.info("retrieving event with id %s", event_id)
    event_document = mongo.find_one(Collections.EVENTS, {'_id': ObjectId(event_id)})

    if event_document is None:
        raise ElementNotFoundException(f"no event found with id {event_id}")

    logger.info("found event with id %s!", event_id)
    return Event(**event_document)

def get_event_by_user_and_id(user_id: str, event_id: str) -> Event:
    logger.info("retrieving event with id %s", event_id)

    if not is_organization_active(user_id):
        raise OrganizationNotActiveException()

    event_document = mongo.find_one(Collections.EVENTS, {'_id': ObjectId(event_id)})

    if event_document is None:
        raise ElementNotFoundException(f"no event found with id {event_id}")

    logger.info("found event with id %s!", event_id)
    return Event(**event_document)

def create_event(user_id: str, request: CreateEventRequest):
    logger.info("storing event..")

    organization = get_organization_by_user_id(user_id)
    if organization.status == OrganizationStatus.PENDING.name:
        raise OrganizationNotActiveException()

    event = Event.from_create_req(request, organization.user_id, organization.coordinates)
    event.created_at = datetime.now(timezone.utc)
    result = mongo.insert_one(Collections.EVENTS, event.model_dump(exclude={"id"}))

    logger.info("event stored with id %s!", result.inserted_id)

    return str(result.inserted_id)

def update_event(user_id: str, event_id: str, update_event_req: UpdateEventRequest):
    logger.info("updating event with id %s..", event_id)
    stored_event = get_event_by_user_and_id(user_id, event_id)

    if not stored_event:
        raise ElementNotFoundException(f"no event found with id {event_id}")

    stored_event.update_by(update_event_req)
    stored_event.updated_at = datetime.now(timezone.utc)

    mongo.update_one(Collections.EVENTS, {'_id': ObjectId(event_id)},
                           {"$set": stored_event.model_dump(exclude={'id'})})

    logger.info("updated event with id %s", event_id)

    return stored_event.id

def delete_event(user_id: str, event_id: str):
    logger.info("deleting event with id %s", event_id)

    if not is_organization_active(user_id):
        raise OrganizationNotActiveException()

    result = mongo.update_one(
        Collections.EVENTS,
        {"_id": ObjectId(event_id)},
        {"$set": {"deleted_at": datetime.now(timezone.utc)}}
    )

    if result.matched_count == 0:
        raise ElementNotFoundException(f"no itinerary found with id {event_id}!")

    logger.info("deleted itinerary with id %s!", event_id)

def search_events(user_id: str, paginated: Paginated) -> PaginatedResponse:
    found_events = []
    filters = {"user_id": user_id}

    logger.info("searching for events for user with id %s..", user_id)

    if not is_organization_active(user_id):
        raise OrganizationNotActiveException()

    cursor = mongo.aggregate(
        Collections.EVENTS,
        filters,
        [{"$sort": {"created_at": -1}},
        {"$skip": paginated.elements_to_skip},
        {"$limit": paginated.page_size}]
    )
    total_events = mongo.count_documents(Collections.EVENTS, filters)

    for ev in list(cursor):
        found_events.append(Event(**ev).model_dump())

    logger.info("found %d events for user with id %s!", len(found_events), user_id)

    return PaginatedResponse(
        content=found_events,
        total_elements=total_events,
        page_size=paginated.page_size,
        page_number=paginated.page_number
    )

