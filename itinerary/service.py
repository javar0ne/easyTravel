import json
import logging
import threading
from io import BytesIO
from datetime import datetime, timezone, timedelta

from bson import ObjectId

from common.assistant import ask_assistant, Conversation, ConversationRole
from common.exceptions import ElementNotFoundException
from common.extensions import CITY_KEY_SUFFIX, CITY_DESCRIPTION_SYSTEM_INSTRUCTIONS, DAILY_EXPIRE, \
    redis_city_description, ITINERARY_SYSTEM_INSTRUCTIONS, db, CITY_DESCRIPTION_USER_PROMPT, ITINERARY_USER_PROMPT, \
    ITINERARY_DAILY_PROMPT
from common.model import PaginatedResponse, Paginated
from common.pdf import PdfItinerary
from itinerary.model import CityDescription, AssistantItineraryResponse, ItineraryRequestStatus, ItineraryRequest, \
    Activity, Budget, TravellingWith, COLLECTION_NAME, Itinerary, ShareWithRequest, PublishReqeust, ItineraryStatus, \
    DuplicateRequest, ItinerarySearch, ItineraryMeta, DateNotValidException, CityDescriptionNotFoundException, \
    UpdateItineraryRequest, CannotUpdateItineraryException

logger = logging.getLogger(__name__)
itineraries = db[COLLECTION_NAME]

def get_itinerary_by_id(itinerary_id) -> Itinerary:
    logger.info("retrieving itinerary with id %s", itinerary_id)
    itinerary_document = itineraries.find_one({'_id': ObjectId(itinerary_id), "deleted_at": None})

    if itinerary_document is None:
        raise ElementNotFoundException(f"no itinerary found with id {itinerary_id}")

    logger.info("found itinerary with id %s", itinerary_id)
    return Itinerary(**itinerary_document)

def get_itineraries_allow_to_daily_schedule() -> list[Itinerary]:
    logger.info("retrieving itineraries allow to daily schedule")
    found_itineraries = []

    cursor = itineraries.find({
        '$and': [
            {"start_date": {"$lte": datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)}},
            {"end_date": {"$gte": datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)}},
            {"reminder_notification": True},
            {"deleted_at": None}
        ]})
    itinerary_documents = list(cursor)
    if len(itinerary_documents) == 0:
        raise ElementNotFoundException("no itinerary found")

    for it in itinerary_documents:
        found_itineraries.append(Itinerary(**it))

    logger.info("found %d itineraries allow to daily schedule", len(found_itineraries))
    return found_itineraries

def create_itinerary(itinerary_request_id: str) -> str:
    logger.info("storing itinerary..")
    stored_itinerary_request = db["itinerary_requests"].find_one({'_id': ObjectId(itinerary_request_id)})

    if stored_itinerary_request is None:
        raise ElementNotFoundException(f"no itinerary request found with id {itinerary_request_id}")

    itinerary = Itinerary.from_document(stored_itinerary_request)
    itinerary.created_at = datetime.now(timezone.utc)
    result = itineraries.insert_one(itinerary.model_dump(exclude={'id'}))

    itinerary_meta = ItineraryMeta(itinerary_id=result.inserted_id)
    db["itinerary_metas"].insert_one(itinerary_meta.model_dump(exclude={'id'}))

    db["itinerary_requests"].delete_one({'_id': ObjectId(itinerary_request_id)})
    logger.info("itinerary stored successfully with id %s", result.inserted_id)

    return str(result.inserted_id)

def update_itinerary(itinerary_id: str, updated_itinerary_req: UpdateItineraryRequest):
    logger.info("updating itinerary with id %s", itinerary_id)

    stored_itinerary = get_itinerary_by_id(itinerary_id)

    if not stored_itinerary:
        raise ElementNotFoundException(f"no itinerary found with id {itinerary_id}")
    if stored_itinerary.status != ItineraryStatus.PENDING.name:
        raise CannotUpdateItineraryException(f"itinerary {stored_itinerary.id} cannot be updated as its status is {stored_itinerary.status}!")

    stored_itinerary.update_by(updated_itinerary_req)
    stored_itinerary.update_at = datetime.now(timezone.utc)
    itineraries.update_one(
        {'_id': ObjectId(itinerary_id)},
        {"$set": updated_itinerary_req.model_dump(exclude={'id'})}
    )

    logger.info("updated itinerary with id %s", itinerary_id)

def delete_itinerary(itinerary_id: str):
    logger.info("deleting itinerary with id %s", itinerary_id)

    result = itineraries.update_one({"_id": ObjectId(itinerary_id)}, {"$set": {"deleted_at": datetime.now(timezone.utc)}})

    if result.matched_count == 0:
        raise ElementNotFoundException(f"no itinerary found with id {itinerary_id}!")

    logger.info("deleted itinerary with id %s!", itinerary_id)

def search_itineraries(itinerary_search: ItinerarySearch) -> PaginatedResponse:
    pipeline = []
    filters = {"deleted_at": None}
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

    pipeline.append({"$match": filters})
    pipeline.append({"$project": {"details": 0}})
    pipeline.append({"$sort": {"created_at": -1}})
    pipeline.append({"$skip": itinerary_search.elements_to_skip})
    pipeline.append({"$limit": itinerary_search.page_size})

    cursor = itineraries.aggregate(pipeline)
    total_itineraries = itineraries.count_documents(filters)

    for it in list(cursor):
        found_itineraries.append(Itinerary(**it).model_dump())

    logger.info("found %d itineraries!", len(found_itineraries))

    return PaginatedResponse(
        content=found_itineraries,
        total_elements=total_itineraries,
        page_size=itinerary_search.page_size,
        page_number=itinerary_search.page_number
    )

def get_completed_itineraries(user_id: str) -> list[Itinerary]:
    found_itineraries = []

    logger.info("searching for completed itineraries..")

    cursor = itineraries.aggregate([
        {"$match": {"user_id": user_id, "shared_with": user_id, "status": ItineraryStatus.COMPLETED.name, "deleted_at": None}},
        {"$sort": {"created_at": -1}},
        {"$project": {"details": 0}}
    ])

    for it in list(cursor):
        found_itineraries.append(Itinerary(**it))

    logger.info("found %d itineraries completed!", len(found_itineraries))

    return found_itineraries

def get_saved_itineraries(user_id: str, paginated: Paginated) -> PaginatedResponse:
    found_itineraries = []

    logger.info("searching for saved itineraries by user with id %s..", user_id)

    cursor = db["itinerary_metas"].find({"saved_by": user_id}, {"itinerary_id": 1})
    saved_itineraries = [ObjectId(it["itinerary_id"]) for it in list(cursor)]

    filters = {"_id": {"$in": saved_itineraries}, "deleted_at": None}
    cursor = itineraries.aggregate([
        {"$match": filters},
        {"$sort": {"created_at": -1}},
        {"$project": {"details": 0}},
        {"$skip": paginated.elements_to_skip},
        {"$limit": paginated.page_size}
    ])
    total_itineraries = itineraries.count_documents(filters)

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
    shared_with_filter = {"shared_with": user_id, "deleted_at": None}

    logger.info("searching for shared itineraries for user id %s..", user_id)

    cursor = itineraries.aggregate([
        {"$match": shared_with_filter},
        {"$project": {"details": 0}},
        {"$sort": {"created_at": -1}},
        {"$skip": paginated.elements_to_skip},
        {"$limit": paginated.page_size}

    ])
    total_itineraries = itineraries.count_documents(shared_with_filter)

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

    result = itineraries.update_one(
        {"_id": ObjectId(share_with_req.id), "deleted_at": None},
        {"$push": {"shared_with": {"$each": share_with_req.users}}}
    )

    if result.matched_count == 0:
        raise ElementNotFoundException(f"no itinerary found with id {share_with_req.id}")

    logger.info("shared itinerary %s with users %s!", share_with_req.id, ','.join(share_with_req.users))

def publish(publish_req: PublishReqeust):
    logger.info("setting itinerary %s is_public field to %s..", publish_req.id, publish_req.is_public)

    result = itineraries.update_one(
        {"_id": ObjectId(publish_req.id), "deleted_at": None},
        {"$set": {"is_public": publish_req.is_public}}
    )

    if result.matched_count == 0:
        raise ElementNotFoundException(f"no itinerary found with id {publish_req.id}")

    logger.info("set itinerary %s is_public field to %s!", publish_req.id, publish_req.is_public)

def completed(itinerary_id: str):
    logger.info("marking itinerary %s as completed..", itinerary_id)

    result = itineraries.update_one(
        {"_id": ObjectId(itinerary_id), "deleted_at": None},
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

    result = itineraries.insert_one(itinerary.model_dump(exclude={'id'}))

    logger.info("duplicated itinerary %s for user with id!", duplicate_req.id, user_id)

    return str(result.inserted_id)

def get_city_description(city: str) -> CityDescription:
    city_key = f"{city.lower().replace(' ', '-')}-{CITY_KEY_SUFFIX}"
    if redis_city_description.exists(city_key):
        city_description = json.loads(redis_city_description.get(city_key))
        return CityDescription(**city_description)

    conversation = Conversation(CityDescription)
    conversation.add_message_from(CITY_DESCRIPTION_SYSTEM_INSTRUCTIONS)
    conversation.add_message(ConversationRole.USER.value, CITY_DESCRIPTION_USER_PROMPT.format(city=city))

    city_description = ask_assistant(conversation)

    if city_description is None:
        raise CityDescriptionNotFoundException("City description not found.")

    redis_city_description.set(city_key, json.dumps(city_description.model_dump()), DAILY_EXPIRE)

    return city_description

def get_itinerary_request_by_id(request_id: str) -> ItineraryRequest:
    logger.info("retrieving itinerary request with id %s", request_id)

    itinerary_request = db["itinerary_requests"].find_one({"_id": ObjectId(request_id)})
    if not itinerary_request:
        raise ElementNotFoundException(f"no itinerary request found with id {request_id}")

    return ItineraryRequest(**itinerary_request)

def generate_itinerary_request(itinerary_request: ItineraryRequest) -> str:
    logger.info("generating itinerary request..")

    if itinerary_request.start_date < datetime.today().astimezone(timezone.utc):
        raise DateNotValidException("start date must be greater or equal to today")

    request_id = db["itinerary_requests"].insert_one(itinerary_request.model_dump()).inserted_id
    conversation = Conversation(AssistantItineraryResponse)
    conversation.add_message_from(ITINERARY_SYSTEM_INSTRUCTIONS)

    threading.Thread(target=generate_day_by_day, args=(conversation, request_id, itinerary_request)).start()

    return request_id

def generate_day_by_day(conversation: Conversation, request_id: ObjectId, itinerary_request: ItineraryRequest):
    logger.info("starting itinerary generation..")
    trip_duration = (itinerary_request.end_date - itinerary_request.start_date).days + 1
    month = itinerary_request.start_date.strftime("%B")
    interested_in = ','.join(Activity[activity].value for activity in itinerary_request.interested_in)
    budget = Budget[itinerary_request.budget]
    travelling_with = TravellingWith[itinerary_request.travelling_with]

    conversation.add_message(
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

    for day in range(1,trip_duration + 1):
        try:
            logger.info("starting day %d itinerary generation..", day)
            conversation.add_message(
                ConversationRole.USER.value,
                ITINERARY_DAILY_PROMPT.format(day=day)
            )

            logger.info("asking assistant..")

            itinerary_response = ask_assistant(conversation)

            logger.info("assistant answered with: %s", itinerary_response.itinerary[0].model_dump())

            db["itinerary_requests"].update_one(
                {"_id": request_id},
                {"$push": {"details": itinerary_response.itinerary[0].model_dump()}}
            )

            conversation.add_message(ConversationRole.ASSISTANT.value, f"{itinerary_response.model_dump()}")
            logger.info("completed day %d", day)
        except Exception as err:
            logger.error(str(err))
            db["itinerary_requests"].update_one({"_id": request_id},{"$set": {"status": ItineraryRequestStatus.ERROR.name}})
            logger.info("error on day %d", day)
            logger.info("stopped itinerary generation!")
            return

    db["itinerary_requests"].update_one({"_id": request_id}, {"$set": {"status": ItineraryRequestStatus.COMPLETED.name}})
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
    itineraries.update_one(
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