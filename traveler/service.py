import logging
from datetime import datetime, timezone

from bson import ObjectId

from common.exceptions import ElementNotFoundException
from common.extensions import db
from common.role import Role
from traveler.model import COLLECTION_NAME, TravelerCreateRequest, UpdateTravelerRequest, Traveler
from user.service import create_user

logger = logging.getLogger(__name__)
travelers = db[COLLECTION_NAME]

def exists_by_id(traveler_id: str) -> bool:
    return travelers.count_documents({"_id": ObjectId(traveler_id)}) > 0

def get_traveler_by_id(traveler_id: str) -> Traveler:
    logger.info("retrieving traveler with id %s", traveler_id)
    traveler_document = travelers.find_one({'_id': ObjectId(traveler_id), "deleted_at": None})

    if traveler_document is None:
        raise ElementNotFoundException(f"no traveler found with id: {traveler_id}")

    logger.info("found traveler with id %s", traveler_id)
    return Traveler(**traveler_document)

def get_traveler_by_user_id(user_id: str) -> Traveler:
    logger.info("retrieving traveler with user id %s", user_id)
    traveler_document = travelers.find_one({'user_id': user_id, "deleted_at": None})

    if traveler_document is None:
        raise ElementNotFoundException(f"no traveler found with user id: {user_id}")

    logger.info("found traveler with user id %s", user_id)
    return Traveler(**traveler_document)

def create_traveler(request: TravelerCreateRequest) -> str:
    logger.info("storing traveler..")
    user_id = create_user(request.email, request.password, [Role.TRAVELER.name])

    request.user_id = str(user_id)
    traveler = Traveler.from_create_req(request)
    traveler.created_at = datetime.now(timezone.utc)
    stored_traveler = travelers.insert_one(traveler.model_dump())
    logger.info("traveler stored successfully with id %s", stored_traveler.inserted_id)

    return str(stored_traveler.inserted_id)

def update_traveler(traveler_id: str, updated_traveler: UpdateTravelerRequest):
    logger.info("updating traveler with id %s..", traveler_id)
    stored_traveler = get_traveler_by_id(traveler_id)
    if not stored_traveler:
        raise ElementNotFoundException(f"no traveler found with id: {traveler_id}")

    stored_traveler.update_by(updated_traveler)
    stored_traveler.update_at = datetime.now(timezone.utc)
    travelers.update_one({'_id': ObjectId(traveler_id)}, {'$set': updated_traveler.model_dump()})
    logger.info("traveler with id %s updated successfully", traveler_id)