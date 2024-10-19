import logging
from typing import Optional

from bson import ObjectId

from common.exception import ElementNotFoundException
from common.extensions import db
from common.role import Role
from traveler.model import COLLECTION_NAME, TravelerCreateModel, TravelerUpdateModel
from user.service import create_user

logger = logging.getLogger(__name__)
collection = db[COLLECTION_NAME]

def traveler_exists_by_id(traveler_id: str) -> bool:
    if collection.count_documents({"_id": ObjectId(traveler_id)}) == 0:
        return False

    return True

def get_traveler_by_id(traveler_id: str) -> Optional[dict]:
    logger.info("retrieving traveler with id %s", traveler_id)
    traveler_document = collection.find_one({'_id': ObjectId(traveler_id)})

    if traveler_document is None:
        logger.warning("no traveler found with id %s", traveler_id)
        raise ElementNotFoundException(f"no travler found with id: {traveler_id}")

    logger.info("found traveler with id %s", traveler_id)
    return traveler_document

def create_traveler(traveler: TravelerCreateModel) -> Optional[str]:
    logger.info("storing traveler..")

    user_id = create_user(traveler.email, traveler.password, [Role.TRAVELER.name])

    traveler.user_id = str(user_id)
    stored_traveler = collection.insert_one(traveler.model_dump(exclude={'email', 'password'}))
    logger.info("traveler stored successfully with id %s", stored_traveler.inserted_id)

    return str(stored_traveler.inserted_id)

def update_traveler(traveler_id: str, updated_traveler: TravelerUpdateModel):
    logger.info("updating traveler with id %s..", traveler_id)
    if get_traveler_by_id(traveler_id) is None:
        raise ElementNotFoundException(f"no traveler found with id: {traveler_id}")

    collection.update_one({'_id': ObjectId(traveler_id)}, {'$set': updated_traveler.model_dump()})
    logger.info("traveler with id %s updated successfully", traveler_id)