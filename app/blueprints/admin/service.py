import logging

from app.blueprints.admin.model import ItineraryActivationRequest, Config
from app.blueprints.user.service import create_user, exists_admin
from app.extensions import mongo
from app.models import Collections
from app.role import Role

logger = logging.getLogger(__name__)

def config_exists():
    return mongo.get_collection(Collections.ADMIN_CONFIGS).count_documents({}) > 0

def create_admin_user(email: str, password: str):
    if exists_admin():
        logger.info("admin user already exists!")
        return

    logging.info("admin user does not exist, creating it..")
    create_user(email, password, [Role.ADMIN.name])
    logging.info("admin user created!")

def create_initial_config():
    if config_exists():
        logger.info("config already exists!")
        return

    logger.info("config does not exist, creating it..")
    mongo.insert_one(Collections.ADMIN_CONFIGS, Config().model_dump(exclude={'id'}))
    logger.info("config created!")

def can_generate_itinerary():
    projected_configs = mongo.get_collection(Collections.ADMIN_CONFIGS).find_one({}, {"is_itinerary_active": 1})

    return projected_configs.get("is_itinerary_active")

def handle_itinerary_activation(itinerary_activation_req: ItineraryActivationRequest):
    logger.info("updating is_itinerary_active with value %d", itinerary_activation_req.is_itinerary_active)
    mongo.get_collection(Collections.ADMIN_CONFIGS).update_one(
        {},
        {'$set': {"is_itinerary_active": itinerary_activation_req.is_itinerary_active}}
    )
    logger.info("updated is_itinerary_active value!")