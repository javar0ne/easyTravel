from datetime import date

from flask import render_template
from flask_mailman import EmailMessage

from app.blueprints.itinerary.model import Itinerary, AssistantItinerary, AssistantItineraryDocs
from app.blueprints.traveler.model import Traveler
from app.extensions import scheduler


def send_travel_schedule(email: str,
                         traveler: Traveler,
                         itinerary: Itinerary,
                         day_detail: AssistantItinerary):
    with scheduler.app.app_context():
        html_content = render_template(
            "daily_travel_schedule.html",
            city = itinerary.city,
            recipient_name =traveler.first_name + " " + traveler.last_name,
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

def send_docs_reminder(email: str,
                       traveler: Traveler,
                       city: str,
                       docs: AssistantItineraryDocs):
    with scheduler.app.app_context():
        html_content = render_template(
            "docs_reminder.html",
            city = city,
            recipient_name=traveler.first_name + " " + traveler.last_name,
            docs = docs,
            year = date.today().year
        )

        message = EmailMessage(
            subject=f"Reminder docs required for {city}",
            to=[email],
            body = html_content
        )
        message.content_subtype = "html"
        message.send()