from datetime import datetime


from flask import jsonify

def success_response(response, code=200):
    return jsonify({
        "status": "SUCCESS",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "response": response
    }), code

def error_response(code=500):
    return jsonify({
        "status": "FAILURE",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "response": "There was an internal error"
    }), code

def not_found_response(response, code=404):
    return jsonify({
        "status": "FAILURE",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "response": response
    }), code

def unauthorized_response(code=401):
    return jsonify({
        "status": "FAILURE",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }), code

def forbidden_response(code=403):
    return jsonify({
        "status": "FAILURE",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "response": "You are not authorized to access this resource"
    }), code

def bad_request_response(response, code=400):
    return jsonify({
        "status": "FAILURE",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "response": response
    }), code

def conflict_response(response, code=409):
    return jsonify({
        "status": "FAILURE",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "response": response
    }), code

def no_content_response(code=204):
    return jsonify({
        "status": "SUCCESS",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }), code