import json
import logging
import threading
from datetime import datetime, timezone, timedelta
from io import BytesIO

from bson import ObjectId

from app.assistant import Conversation, ConversationRole
from app.blueprints.admin.service import can_generate_itinerary
from app.blueprints.event.service import get_event_by_id
from app.blueprints.itinerary.mail import send_docs_reminder
from app.blueprints.itinerary.model import CityDescription, AssistantItineraryResponse, ItineraryRequestStatus, \
    ItineraryRequest, \
    Activity, Budget, TravellingWith, Itinerary, ShareWithRequest, PublishReqeust, ItineraryStatus, \
    DuplicateRequest, ItinerarySearch, ItineraryMeta, DateNotValidException, CityDescriptionNotFoundException, \
    UpdateItineraryRequest, CannotUpdateItineraryException, ItineraryGenerationDisabledException, DocsNotFoundException, \
    AssistantItineraryDocsResponse, CityDescriptionRequest
from app.blueprints.traveler.service import get_traveler_by_user_id
from app.blueprints.user.service import get_user_by_id
from app.exceptions import ElementNotFoundException
from app.extensions import mongo, assistant, ITINERARY_RETRIEVE_DOCS_PROMPT, CITY_KEY_SUFFIX, redis_city_description, \
    CITY_DESCRIPTION_SYSTEM_INSTRUCTIONS, CITY_DESCRIPTION_USER_PROMPT, DAILY_EXPIRE, ITINERARY_USER_PROMPT, \
    ITINERARY_USER_EVENT_PROMPT, ITINERARY_SYSTEM_INSTRUCTIONS, ITINERARY_DAILY_PROMPT, \
    JOB_NOTIFICATION_DOCS_REMINDER_DAYS_BEFORE_START_DATE
from app.models import PaginatedResponse, Paginated, Collections
from app.pdf import PdfItinerary

logger = logging.getLogger(__name__)

def get_itinerary_by_id(itinerary_id) -> Itinerary:
    logger.info("retrieving itinerary with id %s", itinerary_id)
    itinerary_document = mongo.find_one(Collections.ITINERARIES, {'_id': ObjectId(itinerary_id)})

    if itinerary_document is None:
        raise ElementNotFoundException(f"no itinerary found with id {itinerary_id}")

    logger.info("found itinerary with id %s", itinerary_id)
    return Itinerary(**itinerary_document)

def get_itineraries_allow_to_daily_schedule() -> list[Itinerary]:
    logger.info("retrieving itineraries allow to daily schedule")
    found_itineraries = []

    cursor = mongo.find(
        Collections.ITINERARIES,
        {
            '$and': [
                {"start_date": {"$lte": datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)}},
                {"end_date": {"$gte": datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)}},
                {"reminder_notification": True}
            ]
        }
    )
    itinerary_documents = list(cursor)
    if len(itinerary_documents) == 0:
        raise ElementNotFoundException("no itinerary found")

    for it in itinerary_documents:
        found_itineraries.append(Itinerary(**it))

    logger.info("found %d itineraries allow to daily schedule", len(found_itineraries))
    return found_itineraries

def get_itineraries_allow_to_docs_reminder() -> list[Itinerary]:
    logger.info("retrieving itineraries allow to docs reminder")

    target_date = datetime.today() + timedelta(days=JOB_NOTIFICATION_DOCS_REMINDER_DAYS_BEFORE_START_DATE)

    found_itineraries = []
    cursor = mongo.find(
        Collections.ITINERARIES,
        {
            '$and': [
                {"start_date": target_date.replace(hour=0, minute=0, second=0, microsecond=0)},
                {"necessary_documents": {"$exists": True}},
                {"docs_notification": True},
            ]
        }
    )
    itinerary_documents = list(cursor)
    if len(itinerary_documents) == 0:
        raise ElementNotFoundException("no itinerary found")

    for it in itinerary_documents:
        found_itineraries.append(Itinerary(**it))

    logger.info("found %d itineraries allow to docs reminder", len(found_itineraries))
    return found_itineraries

def create_itinerary(itinerary_request_id: str) -> str:
    logger.info("storing itinerary..")
    stored_itinerary_request = mongo.find_one(Collections.ITINERARY_REQUESTS, {'_id': ObjectId(itinerary_request_id)})

    if stored_itinerary_request is None:
        raise ElementNotFoundException(f"no itinerary request found with id {itinerary_request_id}")

    itinerary = Itinerary.from_document(stored_itinerary_request)
    itinerary.created_at = datetime.now(timezone.utc)
    result = mongo.insert_one(Collections.ITINERARIES, itinerary.model_dump(exclude={'id'}))

    itinerary_meta = ItineraryMeta(itinerary_id=result.inserted_id)
    mongo.insert_one(Collections.ITINERARY_METAS, itinerary_meta.model_dump(exclude={'id'}))

    mongo.delete_one(Collections.ITINERARY_REQUESTS, {'_id': ObjectId(itinerary_request_id)})
    logger.info("itinerary stored successfully with id %s", result.inserted_id)

    threading.Thread(target=ask_itinerary_docs, args=(itinerary.city, result.inserted_id, itinerary.user_id, itinerary.start_date)).start()
    return str(result.inserted_id)

def ask_itinerary_docs(city: str,
                       itinerary_id: id,
                       user_id: str,
                       start_date: datetime):
    logger.info("starting retrieve docs...")

    conversation = Conversation(AssistantItineraryDocsResponse)
    conversation.add_message(
        ConversationRole.USER.value,
        ITINERARY_RETRIEVE_DOCS_PROMPT.format(
            city = city,
            month = start_date.month
        )
    )

    logger.info("asking assistant itinerary docs..")

    docs_response = assistant.ask(conversation)
    if docs_response is None:
        raise DocsNotFoundException("Docs not found.")

    mongo.update_one(
        Collections.ITINERARIES,
        {"_id": itinerary_id},
        {"$set": {"docs": docs_response.docs[0].model_dump()}}
    )

    traveler = get_traveler_by_user_id(user_id)
    user = get_user_by_id(user_id)
    send_docs_reminder(email = user.email,
                       traveler = traveler,
                       city = city,
                       docs = docs_response.docs[0])


def update_itinerary(itinerary_id: str, updated_itinerary_req: UpdateItineraryRequest):
    logger.info("updating itinerary with id %s", itinerary_id)

    stored_itinerary = get_itinerary_by_id(itinerary_id)

    if not stored_itinerary:
        raise ElementNotFoundException(f"no itinerary found with id {itinerary_id}")
    if stored_itinerary.status != ItineraryStatus.PENDING.name:
        raise CannotUpdateItineraryException(f"itinerary {stored_itinerary.id} cannot be updated as its status is {stored_itinerary.status}!")

    stored_itinerary.update_by(updated_itinerary_req)
    stored_itinerary.update_at = datetime.now(timezone.utc)
    mongo.update_one(
        Collections.ITINERARIES,
        {'_id': ObjectId(itinerary_id)},
        {"$set": updated_itinerary_req.model_dump(exclude={'id'})}
    )

    logger.info("updated itinerary with id %s", itinerary_id)

def delete_itinerary(itinerary_id: str):
    logger.info("deleting itinerary with id %s", itinerary_id)

    result = mongo.update_one(
        Collections.ITINERARIES,
        {"_id": ObjectId(itinerary_id)},
        {"$set": {"deleted_at": datetime.now(timezone.utc)}}
    )

    if result.matched_count == 0:
        raise ElementNotFoundException(f"no itinerary found with id {itinerary_id}!")

    logger.info("deleted itinerary with id %s!", itinerary_id)

def search_itineraries(itinerary_search: ItinerarySearch) -> PaginatedResponse:
    aggregations = []
    filters = {}
    found_itineraries = []

    logger.info("searching for itineraries..")

    if itinerary_search.city:
        filters["city"] = itinerary_search.city
    if Budget[itinerary_search.budget] != Budget.NONE:
        filters["budget"] = itinerary_search.budget
    if TravellingWith[itinerary_search.travelling_with] != TravellingWith.NONE:
        filters["travelling_with"] = {"$in": {"$each": itinerary_search.travelling_with}}
    if itinerary_search.interested_in:
        filters["interested_in"] = {"$in": {"$each": itinerary_search.interested_in}}

    aggregations.append({"$project": {"details": 0, "docs": 0}})
    aggregations.append({"$sort": {"created_at": -1}})
    aggregations.append({"$skip": itinerary_search.elements_to_skip})
    aggregations.append({"$limit": itinerary_search.page_size})

    cursor = mongo.aggregate(Collections.ITINERARIES, filters, aggregations)
    total_itineraries = mongo.count_documents(Collections.ITINERARIES, filters)

    for it in list(cursor):
        found_itineraries.append(Itinerary(**it).model_dump())

    logger.info("found %d itineraries!", len(found_itineraries))

    return PaginatedResponse(
        content=found_itineraries,
        total_elements=total_itineraries,
        page_size=itinerary_search.page_size,
        page_number=itinerary_search.page_number
    )

def get_completed_itineraries(user_id: str) -> list:
    found_itineraries = []

    logger.info("searching for completed itineraries..")

    cursor = mongo.aggregate(
        Collections.ITINERARIES,
        {
            "$and": [
                {
                    "$or": [
                        {"user_id": user_id},
                        {"shared_with": user_id}
                    ]

                },
                {"status": ItineraryStatus.COMPLETED.name}
            ]
        },
        [{"$sort": {"created_at": -1}},
        {"$project": {"details": 0, "docs": 0}}]
    )

    for it in list(cursor):
        found_itineraries.append(Itinerary(**it).model_dump())

    logger.info("found %d itineraries completed!", len(found_itineraries))

    return found_itineraries

def get_saved_itineraries(user_id: str, paginated: Paginated) -> PaginatedResponse:
    found_itineraries = []

    logger.info("searching for saved itineraries by user with id %s..", user_id)

    cursor = mongo.find(Collections.ITINERARY_METAS, {"saved_by": user_id}, {"itinerary_id": 1})
    saved_itineraries = [ObjectId(it["itinerary_id"]) for it in list(cursor)]

    filters = {"_id": {"$in": saved_itineraries}}
    cursor = mongo.aggregate(
        Collections.ITINERARIES,
        filters,
        [{"$sort": {"created_at": -1}},
        {"$project": {"details": 0, "docs": 0}},
        {"$skip": paginated.elements_to_skip},
        {"$limit": paginated.page_size}]
    )
    total_itineraries = mongo.count_documents(Collections.ITINERARIES, filters)

    for it in list(cursor):
        found_itineraries.append(Itinerary(**it).model_dump())

    logger.info("found %d itineraries saved by user with id %s!", len(found_itineraries), user_id)

    return PaginatedResponse(
        content=found_itineraries,
        total_elements=total_itineraries,
        page_size=paginated.page_size,
        page_number=paginated.page_number
    )

def get_shared_itineraries(user_id: str, paginated: Paginated) -> PaginatedResponse:
    found_itineraries = []
    shared_with_filter = {"shared_with": user_id}

    logger.info("searching for shared itineraries for user id %s..", user_id)

    cursor = mongo.aggregate(
        Collections.ITINERARIES,
        shared_with_filter,
        [{"$project": {"details": 0, "docs": 0}},
        {"$sort": {"created_at": -1}},
        {"$skip": paginated.elements_to_skip},
        {"$limit": paginated.page_size}]
    )
    total_itineraries = mongo.count_documents(Collections.ITINERARIES, shared_with_filter)

    for it in list(cursor):
        found_itineraries.append(Itinerary(**it).model_dump())

    logger.info("found %d shared itineraries for user id %s!", len(found_itineraries), user_id)

    return PaginatedResponse(
        content=found_itineraries,
        total_elements=total_itineraries,
        page_size=paginated.page_size,
        page_number=paginated.page_number
    )

def share_with(share_with_req: ShareWithRequest):
    logger.info("sharing itinerary %s with users %s", share_with_req.id, ','.join(share_with_req.users))

    result = mongo.update_one(
        Collections.ITINERARIES,
        {"_id": ObjectId(share_with_req.id)},
        {"$push": {"shared_with": {"$each": share_with_req.users}}}
    )

    if result.matched_count == 0:
        raise ElementNotFoundException(f"no itinerary found with id {share_with_req.id}")

    logger.info("shared itinerary %s with users %s!", share_with_req.id, ','.join(share_with_req.users))

def publish(publish_req: PublishReqeust):
    logger.info("setting itinerary %s is_public field to %s..", publish_req.id, publish_req.is_public)

    result = mongo.update_one(
        Collections.ITINERARIES,
        {"_id": ObjectId(publish_req.id)},
        {"$set": {"is_public": publish_req.is_public}}
    )

    if result.matched_count == 0:
        raise ElementNotFoundException(f"no itinerary found with id {publish_req.id}")

    logger.info("set itinerary %s is_public field to %s!", publish_req.id, publish_req.is_public)

def completed(itinerary_id: str):
    logger.info("marking itinerary %s as completed..", itinerary_id)

    result = mongo.update_one(
        Collections.ITINERARIES,
        {"_id": ObjectId(itinerary_id)},
        {"$set": {"status": ItineraryStatus.COMPLETED.name}}
    )

    if result.matched_count == 0:
        raise ElementNotFoundException(f"no itinerary found with id {itinerary_id}")

    logger.info("marked itinerary %s as completed!", itinerary_id)

def duplicate(user_id: str, duplicate_req: DuplicateRequest) -> str:
    logger.info("duplicating itinerary %s for user with id %s..", duplicate_req.id, user_id)

    itinerary = get_itinerary_by_id(duplicate_req.id)
    duration_in_days = (itinerary.end_date - itinerary.start_date).days
    itinerary.start_date = datetime.now(timezone.utc) + timedelta(days=1)
    itinerary.end_date = itinerary.start_date + timedelta(days=duration_in_days)
    itinerary.user_id = user_id
    itinerary.shared_with = []
    itinerary.status = ItineraryStatus.PENDING.name
    itinerary.docs_notification = False
    itinerary.reminder_notification = False
    itinerary.is_public = False
    itinerary.created_at = datetime.now(timezone.utc)
    itinerary.update_at = None
    itinerary.deleted_at = None

    result = mongo.insert_one(Collections.ITINERARIES, itinerary.model_dump(exclude={'id'}))

    logger.info("duplicated itinerary %s for user with id!", duplicate_req.id, user_id)

    return str(result.inserted_id)

def get_city_description(request: CityDescriptionRequest) -> CityDescription:
    city_key = f"{request.name.lower().replace(' ', '-')}-{CITY_KEY_SUFFIX}"
    if redis_city_description.get_client().exists(city_key):
        city_description = json.loads(redis_city_description.get_client().get(city_key))
        return CityDescription(**city_description)

    conversation = Conversation(CityDescription)
    conversation.add_message_from(CITY_DESCRIPTION_SYSTEM_INSTRUCTIONS)
    conversation.add_message(ConversationRole.USER.value, CITY_DESCRIPTION_USER_PROMPT.format(city=request.name))

    city_description = assistant.ask(conversation)

    if city_description is None:
        raise CityDescriptionNotFoundException("City description not found.")

    redis_city_description.get_client().set(city_key, json.dumps(city_description.model_dump()), DAILY_EXPIRE)

    return city_description

def get_itinerary_request_by_id(request_id: str) -> ItineraryRequest:
    logger.info("retrieving itinerary request with id %s", request_id)

    itinerary_request = mongo.find_one(Collections.ITINERARY_REQUESTS, {"_id": ObjectId(request_id)})
    if not itinerary_request:
        raise ElementNotFoundException(f"no itinerary request found with id {request_id}")

    return ItineraryRequest(**itinerary_request)

def handle_itinerary_request(user_id: str, itinerary_request: ItineraryRequest):
    itinerary_request.user_id = user_id

    trip_duration, month, interested_in, budget, travelling_with = generate_itinerary_infos(itinerary_request)
    initial_user_prompt = Conversation.create_message(
        ConversationRole.USER.value,
        ITINERARY_USER_PROMPT.format(
            month=month,
            city=itinerary_request.city,
            travelling_with=travelling_with.value,
            trip_duration=trip_duration,
            min_budget=budget.min,
            max_budget=budget.max,
            interested_in=interested_in
        )
    )

    return generate_itinerary_request(itinerary_request, initial_user_prompt, trip_duration)


def handle_event_itinerary_request(traveler_id: str, itinerary_request: ItineraryRequest, event_id: str):
    itinerary_request.user_id = traveler_id
    event = get_event_by_id(event_id)

    trip_duration, month, interested_in, budget, travelling_with = generate_itinerary_infos(itinerary_request)
    initial_user_prompt = Conversation.create_message(
        ConversationRole.USER.value,
        ITINERARY_USER_EVENT_PROMPT.format(
            month=month,
            city=itinerary_request.city,
            travelling_with=travelling_with.value,
            trip_duration=trip_duration,
            min_budget=budget.min,
            max_budget=budget.max,
            interested_in=interested_in,
            event_period=event.period,
            event_title=event.title,
            event_description=event.description,
            event_cost=event.cost,
            event_accessible=event.accessible,
            event_lat=event.coordinates.lat,
            event_lng=event.coordinates.lng,
            event_avg_duration=event.avg_duration
        )
    )

    return generate_itinerary_request(itinerary_request, initial_user_prompt, trip_duration)

def generate_itinerary_request(itinerary_request: ItineraryRequest, initial_user_prompt: dict, trip_duration: int) -> str:
    logger.info("generating itinerary request..")

    if not can_generate_itinerary():
        raise ItineraryGenerationDisabledException()

    if itinerary_request.start_date < datetime.today().astimezone(timezone.utc):
        raise DateNotValidException("start date must be greater or equal to today")

    request_id = mongo.insert_one(Collections.ITINERARY_REQUESTS, itinerary_request.model_dump()).inserted_id
    conversation = Conversation(AssistantItineraryResponse)
    conversation.add_message_from(ITINERARY_SYSTEM_INSTRUCTIONS)
    conversation.add_message_from(initial_user_prompt)

    threading.Thread(target=generate_day_by_day,args=(conversation, request_id, trip_duration)).start()

    return request_id

def generate_itinerary_infos(itinerary_request: ItineraryRequest):
    trip_duration = (itinerary_request.end_date - itinerary_request.start_date).days + 1
    month = itinerary_request.start_date.strftime("%B")
    interested_in = ','.join(Activity[activity].value for activity in itinerary_request.interested_in)
    budget = Budget[itinerary_request.budget]
    travelling_with = TravellingWith[itinerary_request.travelling_with]

    return trip_duration, month, interested_in, budget, travelling_with

def generate_day_by_day(conversation: Conversation, request_id: ObjectId, trip_duration: int):
    logger.info("starting itinerary generation..")

    for day in range(1,trip_duration + 1):
        try:
            logger.info("starting day %d itinerary generation..", day)
            conversation.add_message(
                ConversationRole.USER.value,
                ITINERARY_DAILY_PROMPT.format(day=day)
            )

            logger.info("asking assistant..")

            itinerary_response = assistant.ask(conversation)

            mongo.update_one(
                Collections.ITINERARY_REQUESTS,
                {"_id": request_id},
                {"$push": {"details": itinerary_response.itinerary[0].model_dump()}}
            )

            conversation.add_message(ConversationRole.ASSISTANT.value, f"{itinerary_response.model_dump()}")
            logger.info("completed day %d", day)
        except Exception as err:
            logger.error(str(err))

            mongo.update_one(
                Collections.ITINERARY_REQUESTS,
                {"_id": request_id},
                {"$set": {"status": ItineraryRequestStatus.ERROR.name}}
            )

            logger.info("error on day %d", day)
            logger.info("stopped itinerary generation!")
            return

    mongo.update_one(
        Collections.ITINERARY_REQUESTS,
        {"_id": request_id},
        {"$set": {"status": ItineraryRequestStatus.COMPLETED.name}}
    )
    logger.info("completed itinerary generation!")

def download_itinerary(itinerary_id) -> BytesIO:
    itinerary = get_itinerary_by_id(itinerary_id)
    logger.info("generate pdf for itinerary with id %s", itinerary)

    buffer = BytesIO()
    doc = PdfItinerary(buffer)
    doc.draw_header(itinerary)
    doc.draw_itinerary_information(itinerary)
    doc.draw_days_itinerary(itinerary)
    doc.save()
    buffer.seek(0)
    return buffer

def update_itinerary_status(itinerary_id: str,
                            status: ItineraryStatus):
    mongo.update_one(
        Collections.ITINERARIES,
        {'_id': ObjectId(itinerary_id)},
        {"status": status.name}
    )
    logger.info("updated status of itinerary with id %s", itinerary_id)

def check_itinerary_started(itinerary):
    delta = datetime.today() - itinerary.start_date
    if delta.days == timedelta(days=0).days:
        update_itinerary_status(itinerary_id=itinerary.id,
                                status=ItineraryStatus.READY)

def check_itinerary_last_day(itinerary):
    delta = datetime.today() - itinerary.end_date
    if delta.days == timedelta(days=0).days:
        update_itinerary_status(itinerary_id=itinerary.id,
                                status=ItineraryStatus.COMPLETED)