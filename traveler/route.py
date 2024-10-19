import logging

from flask import request, jsonify, abort
from pydantic import ValidationError

from traveler import traveler
from traveler.model import TravelerCreateModel, TravelerUpdateModel, TravelerModel
from traveler.service import create_traveler, get_traveler_by_id, update_traveler

logger = logging.getLogger(__name__)

@traveler.get('/<traveler_id>')
def get(traveler_id):
    traveler = get_traveler_by_id(traveler_id)

    if traveler is None:
        return abort(404, description=f'No traveler found with id {traveler_id}')

    return TravelerModel(**traveler).model_dump(), 200

@traveler.post('/')
def create():
    try:
        logger.debug("parsing request body to traveler..")
        traveler_data = TravelerCreateModel(**request.json)
    except ValidationError as err:
        logger.error("validation error while parsing traveler request", err)
        return jsonify(err.errors()), 400

    try:
        inserted_id = create_traveler(traveler_data)
        return jsonify({"_id": inserted_id}), 200
    except Exception as e:
        logger.error(str(e))
        return abort(500)

@traveler.put('/<traveler_id>')
def update(traveler_id):
    try:
        logger.debug("parsing request body to traveler..")
        traveler_data = TravelerUpdateModel(**request.json)
    except ValidationError as err:
        logger.error("validation error while parsing traveler request", err)
        return jsonify(err.errors()), 400

    try:
        result = update_traveler(traveler_id, traveler_data)

        if not result:
            return abort(404, description=f'No traveler found with id {traveler_id}')

        return '', 204
    except Exception as e:
        logger.error(str(e))
        return abort(500)


