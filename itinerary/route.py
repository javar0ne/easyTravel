from common.assistant import get_city_description
from common.response_wrapper import success_response
from itinerary import itinerary


@itinerary.get('/<city_name>')
def get(city_name):
    city_description = get_city_description(city_name)
    return success_response(city_description.model_dump())
