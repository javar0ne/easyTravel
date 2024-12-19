import logging

from app.blueprints.event.mail import send_newsletter
from app.blueprints.event.service import get_events_allow_to_newsletter
from app.blueprints.traveler.service import get_all_travelers
from app.blueprints.user.service import get_user_by_id
from app.exceptions import ElementNotFoundException

logger = logging.getLogger(__name__)

def job_event_newsletter():
    try:
        travelers = get_all_travelers()
        for traveler in travelers:
            user = get_user_by_id(traveler.user_id)
            if len(traveler.interested_in) > 0:
                events = get_events_allow_to_newsletter(traveler.interested_in)
                send_newsletter(email=user.email,traveler=traveler,events=events)

    except ElementNotFoundException as err:
        logger.error(str(err))
        logger.error("no notifications to send.")