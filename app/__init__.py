import logging
import os
from datetime import datetime, timezone

from flask import Flask, request
from flask_jwt_extended import JWTManager

from app.blueprints.admin import admin
from app.blueprints.admin.service import create_admin_user, create_initial_config
from app.blueprints.event import event
from app.blueprints.itinerary import itinerary
from app.blueprints.itinerary.job import job_daily_travel_schedule, job_docs_reminder
from app.blueprints.organization import organization
from app.blueprints.traveler import traveler
from app.blueprints.user import user
from app.blueprints.user.service import is_token_not_valid
from app.config import Config
from app.extensions import mail, scheduler, JOB_NOTIFICATION_DAILY_TRAVEL_TRIGGER, JOB_NOTIFICATION_DAILY_TRAVEL_HOUR, \
    JOB_NOTIFICATION_DAILY_TRAVEL_MINUTES, JOB_NOTIFICATION_DOCS_REMINDER_TRIGGER, JOB_NOTIFICATION_DOCS_REMINDER_HOUR, \
    JOB_NOTIFICATION_DOCS_REMINDER_MINUTES
from app.response_wrapper import not_found_response, unauthorized_response, error_response


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    init_logging()
    init_blueprints(app)
    init_mail(app)
    init_jwt_manager(app)
    init_scheduler(app)
    init_http_interceptors(app)
    init_app()

    return app


def init_logging():
    logging.basicConfig(
        level=os.getenv('LOG_LEVEL', 'DEBUG'),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def init_blueprints(app):
    app.register_blueprint(traveler)
    app.register_blueprint(organization)
    app.register_blueprint(user)
    app.register_blueprint(itinerary)
    app.register_blueprint(event)
    app.register_blueprint(admin)

def init_mail(app):
    mail.init_app(app)

def init_jwt_manager(app):
    jwt = JWTManager(app)

    @jwt.token_in_blocklist_loader
    def check_if_token_not_valid(jwt_header, jwt_payload):
        jti = jwt_payload["jti"]
        jwt_iat = jwt_payload["iat"]
        user_id = jwt_payload["sub"]
        issued_at = datetime.fromtimestamp(jwt_iat, timezone.utc)

        return is_token_not_valid(user_id, issued_at, jti)


def init_scheduler(app):
    scheduler.init_app(app)
    scheduler.start()
    scheduler.add_job(id="job_daily_travel_schedule",
                      func=job_daily_travel_schedule,
                      trigger=JOB_NOTIFICATION_DAILY_TRAVEL_TRIGGER,
                      hour=JOB_NOTIFICATION_DAILY_TRAVEL_HOUR,
                      minute=JOB_NOTIFICATION_DAILY_TRAVEL_MINUTES)
    scheduler.add_job(id="job_docs_reminder",
                      func=job_docs_reminder,
                      trigger=JOB_NOTIFICATION_DOCS_REMINDER_TRIGGER,
                      hour=JOB_NOTIFICATION_DOCS_REMINDER_HOUR,
                      minute=JOB_NOTIFICATION_DOCS_REMINDER_MINUTES)


def init_app():
    create_admin_user()
    create_initial_config()


def init_http_interceptors(app):
    @app.before_request
    def log_request_info():
        if request.path in ['/v1/user/login', '/v1/user/reset-password']:
            app.logger.info(f"Request Info: Method: {request.method}, Path: {request.path}, Body: ***")
        else:
            app.logger.info(
                f"Request Info: Method: {request.method}, Path: {request.path}, Body: {request.get_data(as_text=True)}")

    @app.after_request
    def log_response_info(response):
        app.logger.info(f"Response Info: Status: {response.status}, Path: {request.path}")
        return response

    # handling 404 error
    @app.errorhandler(404)
    def handle_not_found(error):
        return not_found_response({"description": error.description})

    # handling 401 error
    @app.errorhandler(401)
    def handle_unauthorized(error):
        return unauthorized_response({"description": error.description})

    # handling 500 error
    @app.errorhandler(500)
    def handle_internal_server_error(error):
        return error_response()