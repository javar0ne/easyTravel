from datetime import date

from flask import render_template
from flask_mailman import EmailMessage

from common.extensions import scheduler
from itinerary.model import Itinerary, AssistantItinerary
from traveler.model import Traveler


def send_travel_schedule(email: str,
                         traveler: Traveler,
                         itinerary: Itinerary,
                         day_detail: AssistantItinerary):
    with scheduler.app.app_context():
        html_content = render_template(
            "daily_travel_schedule.html",
            city = itinerary.city,
            recipient_name = traveler.name+" "+traveler.surname,
            day = day_detail.day,
            title = day_detail.title,
            stages = day_detail.stages,
            year = date.today().year
        )

        message = EmailMessage(
            subject="Your itinerary for today.",
            to=[email],
            body = html_content
        )
        message.content_subtype = "html"
        message.send()