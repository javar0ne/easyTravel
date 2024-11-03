import logging
from datetime import date

from flask import render_template
from flask_mailman import EmailMessage, EmailMultiAlternatives

from common.extensions import mail
from itinerary.model import AssistantItinerary, Itinerary
from traveler.model import TravelerModel

logger = logging.getLogger(__name__)

def send_forgot_password_mail(email: str, reset_url: str):
    message = EmailMessage(
        subject="Reset your password",
        body=f"Reset your password here {reset_url}!",
        to=[email]
    )
    # message.content_subtype = "html"

    message.send()

def send_travel_schedule(email: str,
                         traveler: TravelerModel,
                         itinerary_document: Itinerary,
                         day_detail: AssistantItinerary):
    html_content = render_template(
        "../itinerary/templates/email/daily_travel_schedule.html",
        city = itinerary_document["city"],
        recipient_name = traveler["name"]+" "+traveler["lastname"],
        day = day_detail["day"],
        title = day_detail["title"],
        stages = day_detail["stages"],
        year = date.today().year
    )

    message = EmailMultiAlternatives(
        subject="Your itinerary for today.",
        to=[email],
        alternatives = [(html_content, "text/html")]
    )
    mail.send(message)
