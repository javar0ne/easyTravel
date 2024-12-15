import logging
import threading
from datetime import datetime, timezone, timedelta, date, time
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
    AssistantItineraryDocsResponse, CityMetaRequest, CityMeta, SpotlightItinerary, ItinerarySearchResponse, \
    ItineraryDetail, ItineraryMetaDetail, ItineraryRequestDetail, UpcomingItinerary, PastItinerary, SavedItinerary
from app.blueprints.traveler.service import get_traveler_by_user_id
from app.blueprints.user.service import get_user_by_id
from app.exceptions import ElementNotFoundException
from app.extensions import mongo, assistant, ITINERARY_RETRIEVE_DOCS_PROMPT, unsplash, redis_itinerary, \
    CITY_DESCRIPTION_SYSTEM_INSTRUCTIONS, CITY_DESCRIPTION_USER_PROMPT, ITINERARY_USER_PROMPT, \
    ITINERARY_USER_EVENT_PROMPT, ITINERARY_SYSTEM_INSTRUCTIONS, ITINERARY_DAILY_PROMPT, \
    JOB_NOTIFICATION_DOCS_REMINDER_DAYS_BEFORE_START_DATE, MOST_SAVED_ITINERARIES_KEY
from app.models import PaginatedResponse, Paginated, Collections, UnsplashImage
from app.pdf import PdfItinerary
from app.utils import encode_city_name

logger = logging.getLogger(__name__)


def find_city_meta(city: str):
    city_meta = mongo.find_one(Collections.CITY_METAS, {"key": encode_city_name(city)})

    if not city_meta:
        return None

    return CityMeta(**city_meta)

def exists_by_id(itinerary_id: str):
    return mongo.exists(Collections.ITINERARIES, {"_id": ObjectId(itinerary_id)})

def get_itinerary_by_id(itinerary_id) -> Itinerary:
    logger.info("retrieving itinerary with id %s", itinerary_id)
    itinerary_document = mongo.find_one(Collections.ITINERARIES, {'_id': ObjectId(itinerary_id)})

    if itinerary_document is None:
        raise ElementNotFoundException(f"no itinerary found with id {itinerary_id}")

    logger.info("found itinerary with id %s", itinerary_id)
    return Itinerary(**itinerary_document)

def get_itinerary_detail(itinerary_id: str) -> Itinerary:
    logger.info("retrieving itinerary detail with id %s", itinerary_id)
    itinerary_document = mongo.find_one(Collections.ITINERARIES, {'_id': ObjectId(itinerary_id)}, { 'docs': 0 })

    if itinerary_document is None:
        raise ElementNotFoundException(f"no itinerary found with id {itinerary_id}")

    logger.info("found itinerary with id %s", itinerary_id)
    itinerary = Itinerary(**itinerary_document)
    city_meta = find_city_meta(itinerary.city)

    return ItineraryDetail.from_sources(itinerary, city_meta)

def get_itinerary_meta(itinerary_id: str) -> ItineraryMeta:
    return mongo.find_one(Collections.ITINERARY_METAS, {"itinerary_id": itinerary_id})

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
        filters["travelling_with"] = itinerary_search.travelling_with
    if itinerary_search.interested_in:
        filters["interested_in"] = {"$in": itinerary_search.interested_in}

    aggregations.append({"$project": {"city": 1, "start_date": 1, "end_date": 1, "interested_in": 1, "travelling_with": 1, "budget": 1}})
    aggregations.append({"$sort": {"created_at": -1}})
    aggregations.append({"$skip": itinerary_search.elements_to_skip})
    aggregations.append({"$limit": itinerary_search.page_size})

    cursor = mongo.aggregate(Collections.ITINERARIES, filters, aggregations)
    total_itineraries = mongo.count_documents(Collections.ITINERARIES, filters)

    for itinerary in list(cursor):
        city_meta = find_city_meta(itinerary.get("city"))
        found_itineraries.append(
            ItinerarySearchResponse(
                id=str(itinerary.get("_id")),
                city=itinerary.get("city"),
                country=city_meta.country,
                description=city_meta.description,
                interested_in=itinerary.get("interested_in"),
                travelling_with=itinerary.get("travelling_with"),
                budget=itinerary.get("budget"),
                start_date=itinerary.get("start_date"),
                end_date=itinerary.get("end_date"),
                image=city_meta.image
            ).model_dump()
        )

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

    logger.info(filters)

    cursor = mongo.aggregate(
        Collections.ITINERARIES,
        filters,
        [{"$sort": {"created_at": -1}},
        {"$project": {"city": 1, "start_date": 1, "end_date": 1, "interested_in": 1}},
        {"$skip": paginated.elements_to_skip},
        {"$limit": paginated.page_size}]
    )
    total_itineraries = mongo.count_documents(Collections.ITINERARIES, filters)

    for it in list(cursor):
        city_meta = find_city_meta(it["city"])
        found_itineraries.append(
            SavedItinerary(
                id=str(it["_id"]),
                city=city_meta.name,
                country=city_meta.country,
                image=city_meta.image,
                start_date=it.get("start_date"),
                end_date=it.get("end_date"),
                interested_in=it.get("interested_in")
            ).model_dump()
        )

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

def get_city_description_by_req(request: CityMetaRequest) -> CityDescription:
    return get_city_description(request.name)

def get_city_description(name: str) -> CityDescription:
    conversation = Conversation(CityDescription)
    conversation.add_message_from(CITY_DESCRIPTION_SYSTEM_INSTRUCTIONS)
    conversation.add_message(ConversationRole.USER.value, CITY_DESCRIPTION_USER_PROMPT.format(city=name))

    city_description = assistant.ask(conversation)

    if city_description is None:
        raise CityDescriptionNotFoundException("City description not found.")

    return city_description

def get_itinerary_request_by_id(request_id: str) -> ItineraryRequestDetail:
    logger.info("retrieving itinerary request with id %s", request_id)

    itinerary_request = mongo.find_one(Collections.ITINERARY_REQUESTS, {"_id": ObjectId(request_id)})
    if not itinerary_request:
        raise ElementNotFoundException(f"no itinerary request found with id {request_id}")

    return ItineraryRequestDetail.from_req(ItineraryRequest(**itinerary_request))

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

    if itinerary_request.start_date < datetime.today():
        raise DateNotValidException("start date must be greater or equal to today")

    request_id = mongo.insert_one(Collections.ITINERARY_REQUESTS, itinerary_request.model_dump(exclude={"id"})).inserted_id
    conversation = Conversation(AssistantItineraryResponse)
    conversation.add_message_from(ITINERARY_SYSTEM_INSTRUCTIONS)
    conversation.add_message_from(initial_user_prompt)

    threading.Thread(target=generate_day_by_day,args=(conversation, request_id, trip_duration)).start()
    threading.Thread(target=retrieve_city_meta, args={itinerary_request.city}).start()

    return request_id


def get_city_image(city: str) -> UnsplashImage:
    logger.info("getting city image for city %s", city)
    response = unsplash.find_one(city)
    logger.info("successfully got image for city %s!", city)

    return response

def retrieve_city_meta(name: str):
    logger.info("getting city %s meta..", name)
    city_meta = find_city_meta(name)

    if not city_meta:
        logger.info("no city meta found for city %s, getting them..", name)

        city_image = get_city_image(encode_city_name(name))
        city_description = get_city_description(name)
        city_meta = CityMeta.from_sources(city_image, city_description)
        mongo.insert_one(Collections.CITY_METAS, city_meta.model_dump(exclude={"id"}))
    else:
        logger.info("city meta for city %s already present!", name)

    logger.info("got city meta for city %s successfully!", name)

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

def handle_save_itinerary(user_id: str, itinerary_id: str):
    logger.info("adding itinerary %s to saved ones for traveler %s..", itinerary_id, user_id)
    itinerary_meta = get_itinerary_meta(itinerary_id)

    if not itinerary_meta:
        logger.warning("no itinerary meta found with id %s", itinerary_id)
        return

    if user_id not in itinerary_meta.get("saved_by"):
        result = mongo.update_one(
            Collections.ITINERARY_METAS,
            {"itinerary_id": itinerary_id},
            {"$push": {"saved_by": user_id}}
        )

        if result.modified_count == 1:
            redis_itinerary.get_client().zincrby(MOST_SAVED_ITINERARIES_KEY, 1, itinerary_id)

        logger.info("itinerary %s saved for user %s!", itinerary_id, user_id)
    else:
        result = mongo.update_one(
            Collections.ITINERARY_METAS,
            {"itinerary_id": itinerary_id},
            {"$pull": {"saved_by": user_id}}
        )

        if result.modified_count == 1:
            redis_itinerary.get_client().zincrby(MOST_SAVED_ITINERARIES_KEY, -1, itinerary_id)

        logger.info("itinerary %s removed from saved for user %s!", itinerary_id, user_id)


def get_most_saved():
    most_saved = redis_itinerary.get_client().zrevrange(name=MOST_SAVED_ITINERARIES_KEY, start=0, end=4, withscores=True)
    itinerary_ids = list(map(lambda x: ObjectId(x[0]), most_saved))
    itineraries = mongo.find(
        Collections.ITINERARIES,
        {"_id": {"$in": itinerary_ids}},
        {"city": 1, "start_date": 1, "end_date": 1, "interested_in": 1, "travelling_with": 1, "budget": 1}
    )
    spotlight_itineraries = []

    for itinerary in itineraries:
        saved_by = filter(lambda x: x[0] == str(itinerary.get("_id")), most_saved)
        city_meta = find_city_meta(itinerary.get("city"))
        spotlight_itineraries.append(
            SpotlightItinerary(
                id=str(itinerary.get("_id")),
                city=itinerary.get("city"),
                country=city_meta.country,
                description=city_meta.description,
                interested_in=itinerary.get("interested_in"),
                travelling_with=itinerary.get("travelling_with"),
                budget=itinerary.get("budget"),
                saved_by=int(next(saved_by)[1]),
                shared_with=itinerary.get("shared_with"),
                start_date=itinerary.get("start_date"),
                end_date=itinerary.get("end_date"),
                image=city_meta.image
            ).model_dump()
        )

    spotlight_itineraries.sort(key=lambda x: x.get("saved_by"), reverse=True)

    return spotlight_itineraries

def get_itinerary_meta_detail(user_id: str, itinerary_id: str):
    itinerary_meta = get_itinerary_meta(itinerary_id)
    document = mongo.find_one(Collections.ITINERARIES, {"_id": ObjectId(itinerary_id)}, {"user_id": 1})
    is_owner = False
    has_saved = False

    if document.get("user_id") == user_id:
        is_owner = True

    if user_id in itinerary_meta.get("saved_by"):
        has_saved = True

    return ItineraryMetaDetail(is_owner=is_owner, has_saved=has_saved)

def get_upcoming_itineraries(user_id: str):
    logger.info({"user_id": user_id, "start_date": { "$gte": datetime.combine(date.today(), time.min, tzinfo=timezone.utc) }})
    cursor = mongo.aggregate(
        Collections.ITINERARIES,
        {"user_id": user_id, "end_date": { "$gte": datetime.combine(date.today(), time.min, tzinfo=timezone.utc) }},
        [
            {
                "$project": {
                    "city": 1,
                    "start_date": 1,
                    "end_date": 1,
                    "interested_in": 1,
                    "travelling_with": 1,
                    "budget": 1,
                    "is_public": 1,
                    "shared_with": 1
                }
            },
            {"$sort": {"start_date": 1}}
        ]
    )
    found_itineraries = []

    for it in list(cursor):
        city_meta = find_city_meta(it.get("city"))
        found_itineraries.append(
            UpcomingItinerary(
                id=str(it.get("_id")),
                city=city_meta.name,
                country=city_meta.country,
                description=city_meta.description,
                image=city_meta.image,
                interested_in=it.get("interested_in"),
                travelling_with=it.get("travelling_with"),
                budget=it.get("budget"),
                start_date=it.get("start_date"),
                end_date=it.get("end_date"),
                shared_with=it.get("shared_with"),
                is_public=it.get("is_public")
            ).model_dump()
        )

    return found_itineraries

def get_past_itineraries(user_id: str):
    cursor = mongo.aggregate(
        Collections.ITINERARIES,
        {"user_id": user_id, "end_date": { "$lt": datetime.now(tz=timezone.utc) }},
        [
            {
                "$project": {
                    "city": 1,
                    "start_date": 1,
                    "end_date": 1,
                    "shared_with": 1
                }
            },
            {"$sort": {"start_date": -1}}
        ]
    )
    found_itineraries = []

    for it in list(cursor):
        city_meta = find_city_meta(it.get("city"))
        found_itineraries.append(
            PastItinerary(
                id=str(it.get("_id")),
                city=city_meta.name,
                country=city_meta.country,
                image=city_meta.image,
                start_date=it.get("start_date"),
                end_date=it.get("end_date"),
                shared_with=it.get("shared_with"),
            ).model_dump()
        )

    return found_itineraries
