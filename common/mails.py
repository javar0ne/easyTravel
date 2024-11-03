import logging

from flask_mailman import EmailMessage


logger = logging.getLogger(__name__)

def send_forgot_password_mail(email: str, reset_url: str):
    message = EmailMessage(
        subject="Reset your password",
        body=f"Reset your password here {reset_url}!",
        to=[email]
    )
    message.send()


