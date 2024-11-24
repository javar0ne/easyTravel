from flask_mailman import EmailMessage


def send_traveler_signup_mail(url: str, email: str):
    message = EmailMessage(
        subject="Signup confirmation!",
        body=f"Your registration has been confirmed! Go to {url} to complete your profile!",
        to=[email]
    )
    message.send()