import logging
from datetime import datetime, timezone

from bson import ObjectId

from app.blueprints.organization.model import CreateOrganizationRequest, Organization, \
    UpdateOrganizationRequest, \
    OrganizationStatus, OrganizationFull
from app.blueprints.user.service import create_user, get_user_by_id, update_user_email
from app.exceptions import ElementNotFoundException
from app.extensions import mongo
from app.models import Paginated, PaginatedResponse, Collections
from app.role import Role

logger = logging.getLogger(__name__)

def is_organization_active(user_id: str) -> bool:
    return mongo.exists(Collections.ORGANIZATIONS, {"user_id": user_id, "status": OrganizationStatus.ACTIVE.name})

def exists_by_id(organization_id: str) -> bool:
    return mongo.count_documents(Collections.ORGANIZATIONS, {"_id": ObjectId(organization_id)}) > 0

def get_organization_by_user_id(user_id: str) -> Organization:
    logger.info("retrieving organization with user id %s", user_id)
    organization_document = mongo.find_one(Collections.ORGANIZATIONS, {'user_id': user_id})

    if organization_document is None:
        raise ElementNotFoundException(f"no organization found with user id {user_id}")

    logger.info("found organization with user id %s", user_id)
    return Organization(**organization_document)

def get_organization_by_id(organization_id: str) -> Organization:
    logger.info("retrieving organization with id %s", organization_id)
    organization_document = mongo.find_one(Collections.ORGANIZATIONS, {'user_id': organization_id})

    if organization_document is None:
        raise ElementNotFoundException("no organization found with id {organization_id}")

    logger.info("found organization with id %s", organization_id)
    return Organization(**organization_document)

def get_full_organization_by_id(organization_id: str) -> OrganizationFull:
    logger.info("retrieving organization with id %s", organization_id)
    organization_document = mongo.find_one(Collections.ORGANIZATIONS, {'user_id': organization_id})

    if organization_document is None:
        raise ElementNotFoundException("no organization found with id {organization_id}")

    user = get_user_by_id(organization_id)
    organization = Organization(**organization_document)

    logger.info("found organization with id %s", organization_id)
    return OrganizationFull.from_sources(organization, user)

def create_organization(organization_create_req: CreateOrganizationRequest) -> str:
    logger.info("storing organization..")

    user_id = create_user(organization_create_req.email, organization_create_req.password,[Role.ORGANIZATION.name])

    organization_create_req.user_id = str(user_id)
    organization = Organization.from_create_req(organization_create_req)
    organization.created_at = datetime.now(timezone.utc)
    stored_organization = mongo.insert_one(Collections.ORGANIZATIONS, organization.model_dump(exclude={"id"}))
    logger.info("organization stored successfully with id %s", stored_organization.inserted_id)

    return str(stored_organization.inserted_id)

def update_organization(user_id: str, updated_organization: UpdateOrganizationRequest):
    logger.info("updating organization with id %s..", user_id)
    stored_organization = get_organization_by_id(user_id)
    if not stored_organization:
        raise ElementNotFoundException(f"no traveler found with id: {user_id}")

    if updated_organization.email:
        update_user_email(user_id, updated_organization.email)

    stored_organization.update_by(updated_organization)
    stored_organization.update_at = datetime.now(timezone.utc)
    mongo.update_one(Collections.ORGANIZATIONS, {'user_id': user_id}, {'$set': stored_organization.model_dump(exclude={'id', 'email'})})
    logger.info("organization with id %s updated successfully", user_id)

def get_pending_organizations(paginated: Paginated) -> PaginatedResponse:
    found_organizations = []
    filters = {"status": OrganizationStatus.PENDING.name}

    logger.info("searching for pending organizations..")

    cursor = mongo.aggregate(
        Collections.ORGANIZATIONS,
        filters,
        [{"$sort": {"created_at": -1}},
        {"$skip": paginated.elements_to_skip},
        {"$limit": paginated.page_size}]
    )
    total_organizations_pending = mongo.count_documents(Collections.ORGANIZATIONS, filters)

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
    result = mongo.update_one(
        Collections.ORGANIZATIONS,
        {"_id": ObjectId(organization_id), "deleted_at": None},
        {'$set': {"status": OrganizationStatus.ACTIVE.name}}
    )

    if result.matched_count == 0:
        raise ElementNotFoundException(f"no organization found with id {organization_id}!")

    logger.info("organization with id %s activated!", organization_id)

