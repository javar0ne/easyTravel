import logging
from datetime import datetime

from common.exceptions import ElementNotFoundException
from itinerary.mail import send_travel_schedule
from itinerary.service import get_itineraries_allow_to_daily_schedule,check_itinerary_last_day, check_itinerary_started
from traveler.service import get_traveler_by_id
from user.service import get_user_by_id

logger = logging.getLogger(__name__)

def job_daily_travel_schedule():
    try:
        itineraries = get_itineraries_allow_to_daily_schedule()
        for itinerary in itineraries:
            check_itinerary_started(itinerary)
            traveler = get_traveler_by_id(itinerary.user_id)
            user = get_user_by_id(traveler.user_id)

            delta = datetime.now() - itinerary.start_date
            current_days = delta.days

            send_travel_schedule(user.email,
                                 traveler = traveler,
                                 itinerary = itinerary,
                                 day_detail = itinerary.details[current_days])
            check_itinerary_last_day(itinerary)
    except ElementNotFoundException as err:
        logger.error(str(err))
        logger.error("no notifications to send.")

