import logging
from datetime import datetime, timezone

from bson import ObjectId

from app.exceptions import ElementNotFoundException
from app.extensions import db
from app.model import Paginated, PaginatedResponse
from app.role import Role
from app.blueprints.organization.model import COLLECTION_NAME, OrganizationCreateRequest, Organization, UpdateOrganizationRequest, \
    OrganizationStatus
from app.blueprints.user.service import create_user

logger = logging.getLogger(__name__)
organizations = db[COLLECTION_NAME]

def exists_by_id(organization_id: str) -> bool:
    return organizations.count_documents({"_id": ObjectId(organization_id)}) > 0

def get_organization_by_id(organization_id: str) -> Organization:
    logger.info("retrieving organization with id %s", organization_id)
    organization_document = organizations.find_one({'_id': ObjectId(organization_id), "deleted_at": None})

    if organization_document is None:
        raise ElementNotFoundException("no organization found with id {organization_id}")

    logger.info("found organization with id %s", organization_id)
    return Organization(**organization_document)

def create_organization(organization_create_req: OrganizationCreateRequest) -> str:
    logger.info("storing organization..")

    user_id = create_user(organization_create_req.email,
                          organization_create_req.password,
                          [Role.ORGANIZATION.name])

    organization_create_req.user_id = str(user_id)
    organization = Organization.from_create_req(organization_create_req)
    organization.created_at = datetime.now(timezone.utc)
    stored_organization = organizations.insert_one(organization.model_dump())
    logger.info("organization stored successfully with id %s", stored_organization.inserted_id)

    return str(stored_organization.inserted_id)

def update_organization(id: str, updated_organization: UpdateOrganizationRequest):
    logger.info("updating organization with id %s..", id)
    stored_organization = get_organization_by_id(id)
    if not stored_organization:
        raise ElementNotFoundException(f"no traveler found with id: {id}")

    stored_organization.update_by(updated_organization)
    stored_organization.update_at = datetime.now(timezone.utc)
    organizations.update_one({'_id': ObjectId(id)}, {'$set': stored_organization.model_dump(exclude={'id'})})
    logger.info("organization with id %s updated successfully", id)

def get_pending_organizations(paginated: Paginated) -> PaginatedResponse:
    found_organizations = []
    filters = {"status": OrganizationStatus.PENDING.name, "deleted_at": None}

    logger.info("searching for pending organizations..")

    cursor = organizations.aggregate([
        {"$match": filters},
        #{"$sort": {"created_at": -1}},
        {"$skip": paginated.elements_to_skip},
        {"$limit": paginated.page_size}

    ])
    total_organizations_pending = organizations.count_documents(filters)

    for org in list(cursor):
        found_organizations.append(Organization(**org).model_dump())

    logger.info("found %d pending organizations!", len(found_organizations))

    return PaginatedResponse(
        content=found_organizations,
        total_elements=total_organizations_pending,
        page_size=paginated.page_size,
        page_number=paginated.page_number
    )

def handle_active_organization(organization_id: str):
    logger.info("activating organization with id %s", organization_id)
    result = organizations.update_one(
        {"_id": ObjectId(organization_id), "deleted_at": None},
       {'$set': {"status": OrganizationStatus.ACTIVE.name}}
    )

    if result.matched_count == 0:
        raise ElementNotFoundException(f"no organization found with id {organization_id}!")

    logger.info("organization with id %s activated!", organization_id)

