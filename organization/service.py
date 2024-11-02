import logging
from typing import Optional

from bson import ObjectId

from common.exceptions import ElementNotFoundException
from common.extensions import db
from common.role import Role
from organization.model import COLLECTION_NAME, OrganizationCreateModel, OrganizationUpdateModel
from user.service import create_user

logger = logging.getLogger(__name__)
organizations = db[COLLECTION_NAME]

def get_organization_by_id(organization_id: str) -> Optional[dict]:
    logger.info("retrieving organization with id %s", organization_id)
    organization_document = organizations.find_one({'_id': ObjectId(organization_id)})

    if organization_document is None:
        raise ElementNotFoundException("no organization found with id {organization_id}")

    logger.info("found organization with id %s", organization_id)
    return organization_document

def create_organization(organization: OrganizationCreateModel) -> Optional[str]:
    logger.info("storing organization..")

    user_id = create_user(organization.email,
                          organization.password,
                          [Role.ORGANIZATION.name])

    organization.user_id = str(user_id)
    stored_organization = organizations.insert_one(organization.model_dump(exclude={"email", "password"}))
    logger.info("organization stored successfully with id %s", stored_organization.inserted_id)

    return str(stored_organization.inserted_id)

def update_organization(id: str, updated_organization: OrganizationUpdateModel) -> bool:
    logger.info("updating organization with id %s..", id)
    if get_organization_by_id(id) is None:
        raise ElementNotFoundException(f"no traveler found with id: {id}")

    organizations.update_one({'_id': ObjectId(id)}, {'$set': updated_organization.model_dump()})
    logger.info("organization with id %s updated successfully", id)