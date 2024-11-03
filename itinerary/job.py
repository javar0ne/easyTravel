import datetime
import logging

from common.exceptions import ElementNotFoundException
from itinerary.mail import send_travel_schedule
from itinerary.model import ItineraryStatus
from itinerary.service import get_itineraries_by_status
from traveler.service import get_traveler_by_id
from user.service import get_user_by_id

logger = logging.getLogger(__name__)

def job_daily_travel_schedule():
    try:
        itineraries = get_itineraries_by_status(ItineraryStatus.READY.name)
        for itinerary in itineraries:
            traveler = get_traveler_by_id(itinerary.user_id)
            user = get_user_by_id(traveler.user_id)

            delta = datetime.datetime.now() - itinerary.start_date
            current_days = delta.days

            send_travel_schedule(user.email,
                                 traveler = traveler,
                                 itinerary = itinerary,
                                 day_detail = itinerary.details[current_days])
    except ElementNotFoundException as err:
        logger.error(str(err))
        logger.error("no notifications to send.")