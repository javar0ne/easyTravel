import json
from typing import Optional

from common.assistant import ask_assistant
from common.extensions import CITY_KEY_SUFFIX, CITY_DESCRIPTION_SYSTEM_INSTRUCTIONS, DAILY_EXPIRE, \
    redis_city_description
from itinerary.model import CityDescription


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