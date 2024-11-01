from common.extensions import db
from itinerary.model import ItineraryStatus

def job_daily_travel_schedule():
    itineraries = db["itineraries"]
    itinerary_list = itineraries.find({"status": ItineraryStatus.READY})
    #todo: sending email