import logging

from admin.model import ItineraryActivationRequest, COLLECTION_NAME, Config
from common.extensions import db, ADMIN_MAIL, ADMIN_PASSWORD
from common.role import Role
from user.service import exists_by_email, create_user, exists_admin

admin_configs = db[COLLECTION_NAME]

logger = logging.getLogger(__name__)

def config_exists():
    return admin_configs.count_documents({}) > 0

def create_admin_user():
    if exists_admin(

    ):
        logger.info("admin user already exists!")
        return

    logging.info("creating admin user..")
    create_user(ADMIN_MAIL, ADMIN_PASSWORD, [Role.ADMIN.name])
    logging.info("admin user created!")

def create_initial_config():
    if config_exists():
        logger.info("config already exists!")
        return

    logger.info("config does not exist, creating it..")
    admin_configs.insert_one(Config().model_dump(exclude={'id'}))
    logger.info("config created!")

def can_generate_itinerary():
    projected_configs = admin_configs.find_one({}, {"is_itinerary_active": 1})

    return projected_configs.get("is_itinerary_active")

def handle_itinerary_activation(itinerary_activation_req: ItineraryActivationRequest):
    logger.info("updating is_itinerary_active with value %d", itinerary_activation_req.is_itinerary_active)
    admin_configs.update_one({}, {'$set': {"is_itinerary_active": itinerary_activation_req.is_itinerary_active}})
    logger.info("updated is_itinerary_active value!")

