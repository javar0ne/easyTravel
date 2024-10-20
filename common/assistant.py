import json

from common.extensions import assistant, redis_city_description, DAILY_EXPIRE
from itinerary.model import CityDescription

city_key_suffix = "itinerary-description"

def get_city_description(city: str) -> CityDescription:
    city_key = f"{city.lower().replace(' ', '-')}-{city_key_suffix}"
    if redis_city_description.exists(city_key):
        city_description = json.loads(redis_city_description.get(city_key))
        return CityDescription(**city_description)

    completion = assistant.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {"role": "system",
             "content": "Answer with a short description of the city provided with its latitude, longitude and name."},
            {"role": "user", "content": f"Provide a short description of {city} city."},
        ],
        response_format=CityDescription
    )

    city_description = completion.choices[0].message.parsed

    redis_city_description.set(city_key, json.dumps(city_description.model_dump()), DAILY_EXPIRE)
    return city_description