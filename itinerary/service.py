import json
import threading
from typing import Optional

from bson import ObjectId

from common.assistant import ask_assistant, logger
from common.extensions import CITY_KEY_SUFFIX, CITY_DESCRIPTION_SYSTEM_INSTRUCTIONS, DAILY_EXPIRE, \
    redis_city_description, ITINERARY_SYSTEM_INSTRUCTIONS, db
from itinerary.model import CityDescription, AssistantItineraryResponse, ItineraryRequestStatus


def get_city_description(city: str) -> Optional[CityDescription]:
    city_key = f"{city.lower().replace(' ', '-')}-{CITY_KEY_SUFFIX}"
    if redis_city_description.exists(city_key):
        city_description = json.loads(redis_city_description.get(city_key))
        return CityDescription(**city_description)

    system_instructions = CITY_DESCRIPTION_SYSTEM_INSTRUCTIONS.copy()
    system_instructions.append({"role": "user", "content": f"Provide a short description of {city} city." })

    city_description = ask_assistant(system_instructions, CityDescription)

    if city_description is None:
        return None

    redis_city_description.set(city_key, json.dumps(city_description.model_dump()), DAILY_EXPIRE)

    return city_description

def generate_itinerary():
    request_id = db["itinerary_requests"].insert_one({"itinerary": [], "status": ItineraryRequestStatus.PENDING.name}).inserted_id
    messages = ITINERARY_SYSTEM_INSTRUCTIONS.copy()

    threading.Thread(target=generate_day_by_day, args=(messages, request_id)).start()

    return request_id

def generate_day_by_day(messages: list[dict], request_id: ObjectId):
    # TODO: refactor
    for day in range(1,5):
        try:
            logger.info("starting day %d", day)
            messages.append(
                {
                    "role": "user",
                    "content": f"i'm going to visit London for 4 days in December, with a range budget per person of 0 to max 500 EUR with my family. i'm interested into food exploration and nightlife. generate the itinerary for day {day}."
                }
            )

            itinerary_response = ask_assistant(messages, AssistantItineraryResponse)

            db["itinerary_requests"].update_one({"_id": request_id}, {"$push": {"itinerary": itinerary_response.itinerary[0].model_dump()}})

            messages.append(
                {
                    "role": "assistant",
                    "content": f"{itinerary_response.model_dump()}"
                }
            )

            logger.info("completed day %d", day)
        except Exception as err:
            logger.error(err)
            db["itinerary_requests"].update_one({"_id": request_id},{"$set": {"status": ItineraryRequestStatus.ERROR.name}})

    db["itinerary_requests"].update_one({"_id": request_id}, {"$set": {"status": ItineraryRequestStatus.COMPLETED.name}})