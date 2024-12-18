import logging
from datetime import datetime, timezone

from bson import ObjectId

from app.blueprints.event.model import Event, UpdateEventRequest, CreateEventRequest, UpcomingEvent, OtherEvent, \
    PastEvent, EventStats
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

    event = Event.from_create_req(request, organization.user_id)
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

def get_upcoming_events(user_id: str, paginated: Paginated) -> PaginatedResponse:
    found_events = []
    filters = {"user_id": user_id}

    logger.info("searching for upcoming events for user with id %s..", user_id)

    if not is_organization_active(user_id):
        raise OrganizationNotActiveException()

    cursor = mongo.aggregate(
        Collections.EVENTS,
        filters,
        [
            {"$sort": {"created_at": -1}},
            {"$project": { "start_date": 1, "end_date": 1, "title": 1 }},
            {"$skip": paginated.elements_to_skip},
            {"$limit": paginated.page_size}
        ]
    )
    total_events = mongo.count_documents(Collections.EVENTS, filters)

    for ev in list(cursor):
        found_events.append(
            UpcomingEvent(
                id=str(ev.get("_id")),
                title=ev.get("title"),
                start_date=ev.get("start_date"),
                end_date=ev.get("end_date")
            ).model_dump()
        )

    logger.info("found %d upcoming events for user with id %s!", len(found_events), user_id)

    return PaginatedResponse(
        content=found_events,
        total_elements=total_events,
        page_size=paginated.page_size,
        page_number=paginated.page_number
    )

def get_other_events(user_id: str):
    found_events = []
    filters = {"user_id": {"$ne": user_id}, "end_date": {"$gte": datetime.now(tz=timezone.utc)}}

    logger.info("searching for other events for user with id %s..", user_id)

    if not is_organization_active(user_id):
        raise OrganizationNotActiveException()

    cursor = mongo.aggregate(
        Collections.EVENTS,
        filters,
        [
            {"$sort": {"created_at": -1}},
            {"$project": { "start_date": 1, "end_date": 1, "title": 1, "related_activities": 1 }},
            {"$limit": 5}
        ]
    )

    for ev in list(cursor):
        found_events.append(
            OtherEvent(
                id=str(ev.get('_id')),
                title=ev.get('title'),
                start_date=ev.get("start_date"),
                end_date=ev.get("end_date"),
                related_activities=ev.get('related_activities')
            ).model_dump()
        )

    logger.info("found %d other events for user with id %s!", len(found_events), user_id)

    return found_events

def get_past_events(user_id: str):
    found_events = []
    filters = {"user_id": user_id, "end_date": {"$lt": datetime.now(tz=timezone.utc)}}

    logger.info("searching for past events for user with id %s..", user_id)

    if not is_organization_active(user_id):
        raise OrganizationNotActiveException()

    cursor = mongo.aggregate(
        Collections.EVENTS,
        filters,
        [
            {"$sort": {"end_date": -1}},
            {"$project": { "title": 1, "start_date": 1, "end_date": 1, "avg_duration": 1, "cost": 1 }},
            {"$limit": 5}
        ]
    )

    for ev in list(cursor):
        found_events.append(
            PastEvent(
                id=str(ev.get('_id')),
                title=ev.get('title'),
                start_date=ev.get("start_date"),
                end_date=ev.get("end_date"),
                avg_duration=ev.get("avg_duration"),
                cost= ev.get("cost")
            ).model_dump()
        )

    logger.info("found %d events for user with id %s!", len(found_events), user_id)

    return found_events

def get_events_stats(user_id: str):
    cursor = mongo.aggregate(
        Collections.EVENTS,
        {"user_id": user_id},
        [
            {
                "$group": {
                    "_id": {"user_id": "$user_id", "city_count": "$city"},
                    "used_time": {"$sum": 1},
                    "last_event_created_at": {"$max": "$created_at"},
                    "events_created": {"$sum": 1},
                    "active_events": {
                        "$sum": {
                            "$cond": [
                                {
                                    "$and": [
                                        {"$lte": ["$start_date", datetime.now(tz=timezone.utc)]},
                                        {"$gte": ["$end_date", datetime.now(tz=timezone.utc)]}
                                    ]
                                },
                                1,
                                0
                            ]
                        }
                    }
                }
            },
            {
                "$sort": {"_id.user_id": 1, "city_count": -1}
            },
            {
                "$group": {
                    "_id": "$_id.user_id",
                    "most_used_city": {"$first": "$_id.city_count"},
                    "last_event_created_at": {"$max": "$last_event_created_at"},
                    "events_created": {"$sum": "$events_created"},
                    "active_events": {"$sum": "$active_events"}
                }
            }
        ]
    )

    events_stats = cursor.next() if cursor._has_next() else {}

    return EventStats(
        most_used_city=events_stats.get('most_used_city', ''),
        last_event_created_at=events_stats.get('last_event_created_at', None),
        events_created=events_stats.get('events_created', 0),
        active_events=events_stats.get('active_events', 0),
    )