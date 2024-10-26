import json
import logging
import threading
from typing import Optional

from bson import ObjectId

from common.assistant import ask_assistant, Conversation, ConversationRole
from common.exception import ElementNotFoundException
from common.extensions import CITY_KEY_SUFFIX, CITY_DESCRIPTION_SYSTEM_INSTRUCTIONS, DAILY_EXPIRE, \
    redis_city_description, ITINERARY_SYSTEM_INSTRUCTIONS, db, CITY_DESCRIPTION_USER_PROMPT, ITINERARY_USER_PROMPT
from itinerary.model import CityDescription, AssistantItineraryResponse, ItineraryRequestStatus, ItineraryRequest, \
    Activity, Budget, TravellingWith, COLLECTION_NAME, Itinerary, ShareWithRequest, PublishReqeust, ItineraryStatus, \
    DuplicateRequest

logger = logging.getLogger(__name__)
itineraries = db[COLLECTION_NAME]

def get_itinerary_by_id(itinerary_id):
    logger.info("retrieving itinerary eith id %s", itinerary_id)
    itinerary_document = itineraries.find_one({'_id': ObjectId(itinerary_id)})

    if itinerary_document is None:
        logger.warning("no itinerary found with id %s", itinerary_id)
        raise ElementNotFoundException(f"no itinerary found with id {itinerary_id}")

    logger.info("found itinerary with id %s", itinerary_document)
    return itinerary_document

def create_itinerary(itinerary_request_id: str) -> Optional[str]:
    logger.info("storing itinerary..")
    stored_itinerary_request = db["itinerary_requests"].find_one({'_id': ObjectId(itinerary_request_id)})

    if stored_itinerary_request is None:
        logger.warning(f"no itinerary request found with id {itinerary_request_id}")
        raise ElementNotFoundException(f"no itinerary request found with id {itinerary_request_id}")

    itinerary = Itinerary.from_request_document(stored_itinerary_request)
    result = itineraries.insert_one(itinerary.model_dump(exclude={'id'}))

    db["itinerary_requests"].delete_one({'_id': ObjectId(itinerary_request_id)})
    logger.info("itinerary stored successfully with id %s", result.inserted_id)

    return str(result.inserted_id)

def share_with(share_with: ShareWithRequest):
    result = itineraries.update_one(
        {"_id": ObjectId(share_with.id)},
        {"$push": {"shared_with": {"$each": share_with.users}}}
    )

    if result.matched_count == 0:
        raise ElementNotFoundException(f"no itinerary found with id {share_with.id}")

def publish(is_public_req: PublishReqeust):
    result = itineraries.update_one(
        {"_id": ObjectId(is_public_req.id)},
        {"$set": {"is_public": is_public_req.is_public}}
    )

    if result.matched_count == 0:
        raise ElementNotFoundException(f"no itinerary found with id {is_public_req.id}")

def completed(itinerary_id: str):
    result = itineraries.update_one({"_id": ObjectId(itinerary_id)}, {"$set": {"status": ItineraryStatus.COMPLETED.name}})

    if result.matched_count == 0:
        raise ElementNotFoundException(f"no itinerary found with id {itinerary_id}")

def duplicate(duplicate_req: DuplicateRequest):
    itinerary_document = get_itinerary_by_id(duplicate_req.id)
    itinerary_document["user_id"] = duplicate_req.user_id

    new_itinerary = Itinerary.from_document(itinerary_document)
    result = itineraries.insert_one(new_itinerary.model_dump(exclude={'id'}))

    return str(result.inserted_id)

def get_city_description(city: str) -> Optional[CityDescription]:
    city_key = f"{city.lower().replace(' ', '-')}-{CITY_KEY_SUFFIX}"
    if redis_city_description.exists(city_key):
        city_description = json.loads(redis_city_description.get(city_key))
        return CityDescription(**city_description)

    conversation = Conversation(CityDescription)
    conversation.add_message_from(CITY_DESCRIPTION_SYSTEM_INSTRUCTIONS)
    conversation.add_message(ConversationRole.USER.value, CITY_DESCRIPTION_USER_PROMPT.format(city=city))

    city_description = ask_assistant(conversation)

    if city_description is None:
        return None

    redis_city_description.set(city_key, json.dumps(city_description.model_dump()), DAILY_EXPIRE)

    return city_description

def get_itinerary_request_by_id(request_id: str) -> ItineraryRequest:
    itinerary_request = db["itinerary_requests"].find_one({"_id": ObjectId(request_id)})
    return ItineraryRequest(**itinerary_request)

def generate_itinerary_request(itinerary_request: ItineraryRequest):
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

    for day in range(1,trip_duration):
        try:
            logger.info("starting day %d", day)
            conversation.add_message(
                ConversationRole.USER.value,
                ITINERARY_USER_PROMPT.format(
                    month=month,
                    city=itinerary_request.city,
                    travelling_with=travelling_with.value,
                    trip_duration=trip_duration,
                    min_budget=budget.min,
                    max_budget=budget.max,
                    interested_in=interested_in,
                    day=day
                )
            )

            itinerary_response = ask_assistant(conversation)

            db["itinerary_requests"].update_one(
                {"_id": request_id},
                {"$push": {"details": itinerary_response.itinerary[0].model_dump()}}
            )

            conversation.add_message(ConversationRole.ASSISTANT.value, f"{itinerary_response.model_dump()}")
            logger.info("completed day %d", day)
        except Exception as err:
            logger.error(err)
            db["itinerary_requests"].update_one({"_id": request_id},{"$set": {"status": ItineraryRequestStatus.ERROR.name}})
            logger.info("error on day %d", day)
            logger.info("stopped itinerary generation!")
            return

    db["itinerary_requests"].update_one({"_id": request_id}, {"$set": {"status": ItineraryRequestStatus.COMPLETED.name}})
    logger.info("completed itinerary generation!")