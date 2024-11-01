import logging
import os

from flask import Flask, request
from flask_jwt_extended import JWTManager
from flask_apscheduler import APScheduler

from common.extensions import redis_auth, JOB_NOTIFICATION_DAILY_TRAVEL_HOUR, JOB_NOTIFICATION_DAILY_TRAVEL_MINUTES
from common.job import notification_daily_travel
from common.response_wrapper import not_found_response, unauthorized_response, error_response
from itinerary import itinerary
from organization import organization
from traveler import traveler
from user import user

app = Flask(__name__)
app.register_blueprint(traveler)
app.register_blueprint(organization)
app.register_blueprint(user)
app.register_blueprint(itinerary)

logging.basicConfig(level=os.getenv('LOG_LEVEL', 'DEBUG'), format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# log requests before processing
@app.before_request
def log_request_info():
    logger.info(f"Request Info: Method: {request.method}, Path: {request.path}, Body: {request.get_data(as_text=True)}")

# log responses after processing
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

app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'default-secret-key')
jwt = JWTManager(app)

@jwt.token_in_blocklist_loader
def check_if_token_in_blacklist(jwt_header, jwt_payload):
    jti = jwt_payload["jti"]
    return redis_auth.exists(jti)

#initializer scheduler
scheduler = APScheduler()
scheduler.add_job(id= "job_daily_travel_schedule", func = notification_daily_travel, trigger = 'cron', hour = JOB_NOTIFICATION_DAILY_TRAVEL_HOUR, minute = JOB_NOTIFICATION_DAILY_TRAVEL_MINUTES)
scheduler.start()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')