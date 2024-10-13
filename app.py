import logging
import os

from flask import Flask, request
from flask_jwt_extended import JWTManager

from common.extensions import redis
from common.response_wrapper import not_found_response, unauthorized_response, error_response
from traveler import traveler
from user import user

app = Flask(__name__)
app.register_blueprint(traveler)
app.register_blueprint(user)

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
def handle_not_found(error):
    return unauthorized_response({"description": error.description})

# handling 500 error
@app.errorhandler(500)
def handle_not_found():
    return error_response()

app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'default-secret-key')
jwt = JWTManager(app)

@jwt.token_in_blocklist_loader
def check_if_token_in_blacklist(jwt_header, jwt_payload):
    jti = jwt_payload["jti"]
    return redis.exists(jti)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')