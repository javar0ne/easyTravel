import logging
from typing import Optional

from bson import ObjectId

from common.extensions import db
from common.role import Role
from organization.model import COLLECTION_NAME, Organization
from user.service import create_user

logger = logging.getLogger(__name__)
collection = db[COLLECTION_NAME]

def get_organization_by_id(organization_id: str) -> Optional[Organization]:
    logger.info("retrieving organization with id %s", organization_id)
    organization_document = collection.find_one({'_id': ObjectId(organization_id)})

    if organization_document is None:
        logger.warning("no organization found with id %s", organization_id)
        return None

    logger.info("found organization with id %s", organization_id)
    return organization_document

def create_organization(organization_create_request) -> str:
    logger.info("storing organization..")
    organization_to_store = Organization(
        organization_create_request["phone_number"],
        organization_create_request["currency"],
        organization_create_request["organization_name"],
        organization_create_request["coordinates"],
        organization_create_request["website"],
        organization_create_request["status"]
    )

    user_id = create_user(organization_create_request["email"], organization_create_request["password"], [Role.ORGANIZATION.name])

    organization_to_store.user_id = str(user_id)
    stored_organization = collection.insert_one(organization_to_store.to_dict())
    logger.info("organization stored successfully with id %s", stored_organization.inserted_id)

    return str(stored_organization.inserted_id)

def update_organization(id, updated_organization) -> bool:
    logger.info("updating organization with id %s..", id)
    stored_organization = collection.find_one({'_id': ObjectId(id)})

    if stored_organization is None:
        logger.warning("no organization found with id %s", id)
        return False

    organization_to_store = Organization()
    organization_to_store.email = updated_organization["email"]
    organization_to_store.phone_number = updated_organization["phone_number"]
    organization_to_store.currency = updated_organization["currency"]
    organization_to_store.organization_name = updated_organization["organization_name"]
    organization_to_store.coordinates = updated_organization["coordinates"]
    organization_to_store.website = updated_organization["website"]
    organization_to_store.status = updated_organization["status"]

    collection.update_one({'_id': ObjectId(id)}, {'$set': organization_to_store.to_dict()})
    logger.info("organization with id %s updated successfully", id)

    return True