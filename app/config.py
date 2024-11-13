import os


class Config:
    # mail
    MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = os.getenv("MAIL_PORT", 587)
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER", "no-reply@easytravel.com")

    # jwt
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'default-secret-key')

    # job
    SCHEDULER_API_ENABLED = True