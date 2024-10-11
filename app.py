import logging
import os

from flask import Flask, request, jsonify
from traveler import traveler

def get_logging_level():
    log_level = os.getenv('LOG_LEVEL')
    return log_level if log_level else 'DEBUG'
app = Flask(__name__)
app.register_blueprint(traveler)

logging.basicConfig(level=get_logging_level(), format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
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
    return jsonify({"status": "FAILURE", "description": error.description}), 404

# handling 500 error
@app.errorhandler(500)
def handle_not_found():
    return jsonify({"status": "FAILURE", "description": "There was an internal error"}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')