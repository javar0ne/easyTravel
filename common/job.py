import datetime

from common.exceptions import ElementNotFoundException
from common.mails import send_travel_schedule, logger
from itinerary.model import ItineraryStatus
from itinerary.service import get_itineraries_by_status
from traveler.service import get_traveler_by_id
from user.service import get_user_by_id


def job_daily_travel_schedule():
    try:
        itinerary_documents = get_itineraries_by_status(ItineraryStatus.READY.name)
        for itinerary_document in itinerary_documents:
            user = get_user_by_id(itinerary_document["user_id"])
            if user is None:
                raise ElementNotFoundException(f"user with id {itinerary_document['user_id']} not found")
            traveler_document = get_traveler_by_id(user.id)

            delta = datetime.datetime.now() - itinerary_document["start_date"]
            current_days = delta.days

            send_travel_schedule(user.email,
                                 traveler = traveler_document,
                                 itinerary_document = itinerary_document,
                                 day_detail = itinerary_document["details"][current_days])
    except ElementNotFoundException as err:
        logger.error(str(err))
        logger.error("no notifications to send.")