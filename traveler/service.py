import logging

from common.mongo import db
from traveler.model import TravelerSchema, Traveler, COLLECTION_NAME

logger = logging.getLogger(__name__)
traveler_schema = TravelerSchema()
collection = db[COLLECTION_NAME]

def store(traveler_data):
    logger.debug("parsing traveler data..")
    traveler_to_store = Traveler(
        email=traveler_data["email"],
        password=traveler_data["password"],
        phone_number=traveler_data["phone_number"],
        currency=traveler_data["currency"],
        name=traveler_data["name"],
        surname=traveler_data["surname"],
        birth_date=traveler_data["birth_date"],
        interested_in=traveler_data["interested_in"]
    )

    logger.info("storing traveler %s", traveler_to_store.to_dict())
    stored_traveler = collection.insert_one(traveler_to_store.to_dict())
    logger.info("traveler stored successfully with id %s", stored_traveler.inserted_id)

    return str(stored_traveler.inserted_id)

def get_by_id(traveler_id: int):
    traveler = collection.find_one({'_id': traveler_id})
    return traveler