import logging
from datetime import datetime, timezone

from bson import ObjectId

from app.exceptions import ElementNotFoundException
from app.extensions import db
from app.model import Paginated, PaginatedResponse
from app.blueprints.event.model import Event, COLLECTION_NAME, UpdateEventRequest
from app.blueprints.organization.service import get_organization_by_id

logger = logging.getLogger(__name__)
events = db[COLLECTION_NAME]

def get_event_by_id(event_id: str) -> Event:
    logger.info("retrieving event with id %s", event_id)
    event_document = events.find_one({'_id': ObjectId(event_id), "deleted_at": None})

    if event_document is None:
        raise ElementNotFoundException(f"no event found with id {event_id}")

    logger.info("found event with id %s!", event_id)
    return Event(**event_document)

def create_event(organization_id: str, event: Event):
    logger.info("storing event..")

    organization = get_organization_by_id(organization_id)

    event.coordinates = organization.coordinates
    event.created_at = datetime.now(timezone.utc)
    result = events.insert_one(event.model_dump())

    logger.info("event stored with id %s!", result.inserted_id)

    return str(result.inserted_id)

def update_event(event_id: str, update_event_req: UpdateEventRequest):
    logger.info("updating event with id %s..", event_id)
    stored_event = get_event_by_id(event_id)

    if not stored_event:
        raise ElementNotFoundException(f"no event found with id {event_id}")

    stored_event.update_by(update_event_req)
    stored_event.updated_at = datetime.now(timezone.utc)

    events.update_one(
        {'_id': ObjectId(event_id)},
        {"$set": update_event_req.model_dump(exclude={'id'})}
    )

    logger.info("updated event with id %s", event_id)

def delete_event(event_id: str):
    logger.info("deleting event with id %s", event_id)

    result = events.update_one({"_id": ObjectId(event_id)}, {"$set": {"deleted_at": datetime.now(timezone.utc)}})

    if result.matched_count == 0:
        raise ElementNotFoundException(f"no itinerary found with id {event_id}!")

    logger.info("deleted itinerary with id %s!", event_id)

def search_events(user_id: str, paginated: Paginated) -> PaginatedResponse:
    found_events = []
    filters = {"user_id": user_id, "deleted_at": None}

    logger.info("searching for events for user with id %s..", user_id)

    cursor = events.aggregate([
        {"$match": filters},
        {"$sort": {"created_at": -1}},
        {"$skip": paginated.elements_to_skip},
        {"$limit": paginated.page_size}
    ])
    total_events = events.count_documents(filters)

    for ev in list(cursor):
        found_events.append(Event(**ev).model_dump())

    logger.info("found %d events for user with id %s!", len(found_events), user_id)

    return PaginatedResponse(
        content=found_events,
        total_elements=total_events,
        page_size=paginated.page_size,
        page_number=paginated.page_number
    )

