import logging
from typing import Optional

from bson import ObjectId

from common.extensions import db
from common.role import Role
from traveler.model import COLLECTION_NAME, Traveler
from user.service import create_user

logger = logging.getLogger(__name__)
collection = db[COLLECTION_NAME]

def get_traveler_by_id(traveler_id: str) -> Optional[Traveler]:
    logger.info("retrieving traveler with id %s", traveler_id)
    traveler_document = collection.find_one({'_id': ObjectId(traveler_id)})

    if traveler_document is None:
        logger.warning("no traveler found with id %s", traveler_id)
        return None

    logger.info("found traveler with id %s", traveler_id)
    return traveler_document

def create_traveler(traveler_create_request) -> str:
    logger.info("storing traveler..")
    traveler_to_store = Traveler(
        traveler_create_request["phone_number"],
        traveler_create_request["currency"],
        traveler_create_request["name"],
        traveler_create_request["surname"],
        traveler_create_request["birth_date"],
        traveler_create_request["interested_in"]
    )

    user_id = create_user(traveler_create_request["email"], traveler_create_request["password"], [Role.TRAVELER.name])

    traveler_to_store.user_id = str(user_id)
    stored_traveler = collection.insert_one(traveler_to_store.to_dict())
    logger.info("traveler stored successfully with id %s", stored_traveler.inserted_id)

    return str(stored_traveler.inserted_id)

def update_traveler(id, updated_traveler) -> bool:
    logger.info("updating traveler with id %s..", id)
    stored_traveler = collection.find_one({'_id': ObjectId(id)})

    if stored_traveler is None:
        logger.warning("no traveler found with id %s", id)
        return False

    traveler_to_store = Traveler()
    traveler_to_store.email = updated_traveler["email"]
    traveler_to_store.phone_number = updated_traveler["phone_number"]
    traveler_to_store.currency = updated_traveler["currency"]
    traveler_to_store.name = updated_traveler["name"]
    traveler_to_store.surname = updated_traveler["surname"]
    traveler_to_store.birth_date = updated_traveler["birth_date"]
    traveler_to_store.interested_in = updated_traveler["interested_in"]

    collection.update_one({'_id': ObjectId(id)}, {'$set': traveler_to_store.to_dict()})
    logger.info("traveler with id %s updated successfully", id)

    return True