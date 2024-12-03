import os


class Config:
    # general
    APP_HOST = os.getenv("APP_HOST", "http://127.0.0.1:5000")

    # logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'DEBUG')

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

    # redis
    REDIS_HOST = os.getenv('REDIS_HOST', '127.0.0.1')
    REDIS_PORT = os.getenv('REDIS_PORT', '6379')
    REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', 'admin')

    # mongodb
    MONGO_URI = os.getenv('MONGO_URI', 'mongodb://admin:admin@127.0.0.1:27017/')
    MONGO_DATABASE = os.getenv('MONGO_DATABASE', 'easyTravel')

    # openai
    OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')

    # admin user
    ADMIN_MAIL = os.getenv('ADMIN_MAIL')
    ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD')

    TEMPLATES_AUTO_RELOAD = True

    # unsplash
    UNSPLASH_BASE_URL = os.getenv("UNSPLASH_BASE_URL")
    UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY")
