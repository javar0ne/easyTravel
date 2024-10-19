import logging
from typing import Optional

from bson import ObjectId

from common.extensions import db
from common.role import Role
from traveler.model import COLLECTION_NAME, TravelerModel, TravelerCreateModel, TravelerUpdateModel
from user.service import create_user

logger = logging.getLogger(__name__)
collection = db[COLLECTION_NAME]

def get_traveler_by_id(traveler_id: str) -> Optional[dict]:
    logger.info("retrieving traveler with id %s", traveler_id)
    traveler_document = collection.find_one({'_id': ObjectId(traveler_id)})

    if traveler_document is None:
        logger.warning("no traveler found with id %s", traveler_id)
        return None

    logger.info("found traveler with id %s", traveler_id)
    return traveler_document

def create_traveler(traveler: TravelerCreateModel) -> str:
    logger.info("storing traveler..")
    user_id = create_user(traveler.email, traveler.password, [Role.TRAVELER.name])

    traveler.user_id = str(user_id)
    stored_traveler = collection.insert_one(traveler.model_dump(exclude=['email', 'password']))
    logger.info("traveler stored successfully with id %s", stored_traveler.inserted_id)

    return str(stored_traveler.inserted_id)

def update_traveler(id: str, updated_traveler: TravelerUpdateModel) -> bool:
    logger.info("updating traveler with id %s..", id)
    stored_traveler = collection.find_one({'_id': ObjectId(id)})

    if stored_traveler is None:
        logger.warning("no traveler found with id %s", id)
        return False

    collection.update_one({'_id': ObjectId(id)}, {'$set': updated_traveler.model_dump()})
    logger.info("traveler with id %s updated successfully", id)

    return True