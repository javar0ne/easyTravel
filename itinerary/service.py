import json
import logging
import threading
from io import BytesIO
from datetime import datetime, timezone

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
    DuplicateRequest, ItinerarySearch, ItineraryMeta, DateNotValidException, CityDescriptionNotFoundException

logger = logging.getLogger(__name__)
itineraries = db[COLLECTION_NAME]

def get_itinerary_by_id(itinerary_id) -> Itinerary:
    logger.info("retrieving itinerary with id %s", itinerary_id)
    itinerary_document = itineraries.find_one({'_id': ObjectId(itinerary_id)})

    if itinerary_document is None:
        logger.warning("no itinerary found with id %s", itinerary_id)
        raise ElementNotFoundException(f"no itinerary found with id {itinerary_id}")

    logger.info("found itinerary with id %s", itinerary_document)
    return Itinerary(**itinerary_document)

def get_itineraries_by_status(status) -> list[Itinerary]:
    logger.info("retrieving itineraries with status %s", status)
    found_itineraries = []

    cursor = itineraries.find({"status": status})
    itinerary_documents = list(cursor)
    if len(itinerary_documents) == 0:
        logger.warning("no itinerary found with status %s", status)
        raise ElementNotFoundException(f"no itinerary found with status {status}")

    for it in itinerary_documents:
        found_itineraries.append(Itinerary(**it))

    return found_itineraries

def create_itinerary(itinerary_request_id: str) -> str:
    logger.info("storing itinerary..")
    stored_itinerary_request = db["itinerary_requests"].find_one({'_id': ObjectId(itinerary_request_id)})

    if stored_itinerary_request is None:
        logger.warning(f"no itinerary request found with id {itinerary_request_id}")
        raise ElementNotFoundException(f"no itinerary request found with id {itinerary_request_id}")

    itinerary = Itinerary.from_request_document(stored_itinerary_request)
    result = itineraries.insert_one(itinerary.model_dump(exclude={'id'}))

    itinerary_meta = ItineraryMeta(itinerary_id=result.inserted_id)
    db["itinerary_metas"].insert_one(itinerary_meta.model_dump(exclude={'id'}))

    db["itinerary_requests"].delete_one({'_id': ObjectId(itinerary_request_id)})
    logger.info("itinerary stored successfully with id %s", result.inserted_id)

    return str(result.inserted_id)

def update_itinerary(itinerary_id: str, updated_itinerary: Itinerary):
    logger.info("updating itinerary With id %s", itinerary_id)

    result = itineraries.update_one(
        {'_id': ObjectId(itinerary_id)},
        {"$set": updated_itinerary.model_dump(exclude={'id'})}
    )

    if result.matched_count == 0:
        raise ElementNotFoundException(f"no itinerary found with id {itinerary_id}")

def search_itineraries(itinerary_search: ItinerarySearch) -> PaginatedResponse:
    pipeline = []
    filters = {}
    found_itineraries = []

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
    pipeline.append({"$skip": itinerary_search.elements_to_skip})
    pipeline.append({"$limit": itinerary_search.page_size})

    cursor = itineraries.aggregate(pipeline)
    total_itineraries = itineraries.count_documents(filters)

    for it in list(cursor):
        found_itineraries.append(Itinerary(**it).model_dump())

    return PaginatedResponse(
        content=found_itineraries,
        total_elements=total_itineraries,
        page_size=itinerary_search.page_size,
        page_number=itinerary_search.page_number
    )

def get_completed_itineraries(user_id: str) -> list[Itinerary]:
    found_itineraries = []

    cursor = itineraries.aggregate([
        {"$match": {"user_id": user_id, "status": ItineraryStatus.COMPLETED.name}},
        {"$project": {"details": 0}}
    ])

    for it in list(cursor):
        found_itineraries.append(Itinerary(**it))

    return found_itineraries

def get_shared_itineraries(user_id: str, paginated: Paginated) -> PaginatedResponse:
    found_itineraries = []
    shared_with_filter = {"shared_with": user_id}

    cursor = itineraries.aggregate([
        {"$match": shared_with_filter},
        {"$project": {"details": 0}},
        {"$skip": paginated.elements_to_skip},
        {"$limit": paginated.page_size}

    ])
    total_itineraries = itineraries.count_documents(shared_with_filter)

    for it in list(cursor):
        found_itineraries.append(Itinerary(**it).model_dump())

    return PaginatedResponse(
        content=found_itineraries,
        total_elements=total_itineraries,
        page_size=paginated.page_size,
        page_number=paginated.page_number
    )

def share_with(share_with_req: ShareWithRequest):
    result = itineraries.update_one(
        {"_id": ObjectId(share_with_req.id)},
        {"$push": {"shared_with": {"$each": share_with_req.users}}}
    )

    if result.matched_count == 0:
        raise ElementNotFoundException(f"no itinerary found with id {share_with_req.id}")

def publish(publish_req: PublishReqeust):
    result = itineraries.update_one(
        {"_id": ObjectId(publish_req.id)},
        {"$set": {"is_public": publish_req.is_public}}
    )

    if result.matched_count == 0:
        raise ElementNotFoundException(f"no itinerary found with id {publish_req.id}")

def completed(itinerary_id: str):
    result = itineraries.update_one({"_id": ObjectId(itinerary_id)}, {"$set": {"status": ItineraryStatus.COMPLETED.name}})

    if result.matched_count == 0:
        raise ElementNotFoundException(f"no itinerary found with id {itinerary_id}")

def duplicate(duplicate_req: DuplicateRequest) -> str:
    itinerary = get_itinerary_by_id(duplicate_req.id)
    itinerary.user_id = duplicate_req.user_id

    result = itineraries.insert_one(itinerary.model_dump(exclude={'id'}))
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
    itinerary_request = db["itinerary_requests"].find_one({"_id": ObjectId(request_id)})
    return ItineraryRequest(**itinerary_request)

def generate_itinerary_request(itinerary_request: ItineraryRequest) -> str:
    if itinerary_request.start_date < datetime.today().astimezone(timezone.utc):
        raise DateNotValidException("start date must be greater or equal to today")

    request_id = db["itinerary_requests"].insert_one(itinerary_request.model_dump()).inserted_id
    conversation = Conversation(AssistantItineraryResponse)
    conversation.add_message_from(ITINERARY_SYSTEM_INSTRUCTIONS)

    threading.Thread(target=generate_day_by_day, args=(conversation, request_id, itinerary_request)).start()

    return request_id

def generate_day_by_day(conversation: Conversation, request_id: ObjectId, itinerary_request: ItineraryRequest):
    logger.info("starting itinerary generation..")
    trip_duration = (itinerary_request.end_date - itinerary_request.start_date).days + 2
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

    for day in range(1,trip_duration):
        try:
            logger.info("starting day %d", day)
            conversation.add_message(
                ConversationRole.USER.value,
                ITINERARY_DAILY_PROMPT.format(day=day)
            )

            itinerary_response = ask_assistant(conversation)

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
