from datetime import date

from flask import render_template, url_for
from flask_mailman import EmailMessage

from app.extensions import scheduler
from app.blueprints.event.model import EventNewsletter
from app.blueprints.traveler.model import Traveler


def send_newsletter(email:str,
                    traveler: Traveler,
                    events: list[EventNewsletter]):
    with scheduler.app.app_context():
        html_content = render_template(
            "newsletter.html",
            base_link = url_for("template.generate_itinerary", _external=True),
            traveler = traveler,
            events=events,
            year = date.today().year
        )
        message = EmailMessage(
            subject="Weekly newsletter",
            to=[email],
            body=html_content
        )
        message.content_subtype = "html"
        message.send()