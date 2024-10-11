import logging

from flask import request, jsonify, Blueprint
from marshmallow import ValidationError

from traveler import traveler
from traveler.model import Traveler, TravelerSchema
from traveler.service import store

logger = logging.getLogger(__name__)
traveler_schema = TravelerSchema()

@traveler.get('/<traveler_id>')
def get(traveler_id):
    logger.info(f"retrieving traveler with id {traveler_id}..")
    return f"Hello {traveler_id}"

@traveler.post('/')
def create():
    logger.info("trying to create traveler..")
    try:
        data = request.get_json()
        traveler_data = traveler_schema.load(data)
    except ValidationError as err:
        logger.error("validation error while parsing traveler request", err)
        return jsonify(err.messages), 400

    try:
        inserted_id = store(traveler_data)
        return jsonify({"_id": inserted_id}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

