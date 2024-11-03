import logging
import os
from datetime import timezone, datetime

from flask import Flask, request
from flask_jwt_extended import JWTManager
from flask_apscheduler import APScheduler

from common.extensions import redis_auth, mail, JOB_NOTIFICATION_DAILY_TRAVEL_HOUR, JOB_NOTIFICATION_DAILY_TRAVEL_MINUTES
from common.job import job_daily_travel_schedule
from common.response_wrapper import not_found_response, unauthorized_response, error_response
from itinerary import itinerary
from organization import organization
from traveler import traveler
from user import user
from user.service import is_token_not_valid


app = Flask(__name__)

# mail
app.config['MAIL_SERVER'] = os.getenv("MAIL_SERVER", "smtp.gmail.com")
app.config['MAIL_PORT'] = os.getenv("MAIL_PORT", 587)
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv("MAIL_USERNAME")
app.config['MAIL_PASSWORD'] = os.getenv("MAIL_PASSWORD")  # Your email password
app.config['MAIL_DEFAULT_SENDER'] = os.getenv("MAIL_DEFAULT_SENDER", "no-reply@easytravel.com")

mail.init_app(app)

# blueprint
app.register_blueprint(traveler)
app.register_blueprint(organization)
app.register_blueprint(user)
app.register_blueprint(itinerary)

# logging
logging.basicConfig(level=os.getenv('LOG_LEVEL', 'DEBUG'), format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# request/response interceptors
@app.before_request
def log_request_info():
    if request.path in ['/v1/user/login', '/v1/user/reset-password']:
        logger.info(f"Request Info: Method: {request.method}, Path: {request.path}, Body: ***")
    else:
        logger.info(f"Request Info: Method: {request.method}, Path: {request.path}, Body: {request.get_data(as_text=True)}")

@app.after_request
def log_response_info(response):
    logger.info(f"Response Info: Status: {response.status}, Path: {request.path}")
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

# jwt
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'default-secret-key')
jwt = JWTManager(app)

@jwt.token_in_blocklist_loader
def check_if_token_not_valid(jwt_header, jwt_payload):
    jti = jwt_payload["jti"]
    jwt_iat = jwt_payload["iat"]
    user_id = jwt_payload["sub"]
    issued_at = datetime.fromtimestamp(jwt_iat, timezone.utc)

    return is_token_not_valid(user_id, issued_at, jti)

#initializer scheduler
scheduler = APScheduler()
scheduler.add_job(id= "job_daily_travel_schedule", func = job_daily_travel_schedule, trigger = 'cron', hour = JOB_NOTIFICATION_DAILY_TRAVEL_HOUR, minute = JOB_NOTIFICATION_DAILY_TRAVEL_MINUTES)
scheduler.start()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')