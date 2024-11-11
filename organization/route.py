import logging

from flask import request
from pydantic import ValidationError

from common.exceptions import ElementAlreadyExistsException, ElementNotFoundException
from common.model import Paginated
from common.response_wrapper import bad_request_response, success_response, conflict_response, not_found_response, \
    error_response, no_content_response
from common.role import roles_required, Role
from organization import organization
from organization.model import OrganizationCreateRequest, UpdateOrganizationRequest
from organization.service import create_organization, get_organization_by_id, update_organization, \
    get_pending_organizations, handle_active_organization

logger = logging.getLogger(__name__)

@organization.get('/<organization_id>')
def get(organization_id):
    try:
        organization = get_organization_by_id(organization_id)
        return success_response(organization)
    except ElementNotFoundException as err:
        logger.warning(str(err))
        return not_found_response(err.message)
    except Exception as e:
        logger.error(str(e))
        return bad_request_response(str(e))

@organization.post('/')
def create():
    try:
        logger.debug("parsing request body to organization..")
        organization_create_req = OrganizationCreateRequest(**request.json)

        inserted_id = create_organization(organization_create_req)
        return success_response({"id": inserted_id})
    except ValidationError as err:
        logger.error("validation error while parsing organization request", err)
        return bad_request_response(err.errors())
    except ElementAlreadyExistsException as err:
        logger.error(err.message,err)
        return conflict_response(err.message)
    except Exception as e:
        logger.error(str(e))
        return error_response()

@organization.put('/<organization_id>')
def update(organization_id):
    try:
        logger.debug("parsing request body to organization..")
        organization_data = UpdateOrganizationRequest(**request.json)

        update_organization(organization_id, organization_data)
        return no_content_response()
    except ValidationError as err:
        logger.error("validation error while parsing organization request", err)
        return bad_request_response(err.errors())
    except ElementNotFoundException as err:
        logger.warning(str(err))
        return not_found_response(err.message)
    except Exception as e:
        logger.error(str(e))
        return error_response()

@organization.post('/pending')
@roles_required([Role.ADMIN.name])
def pending_organizations():
    try:
        organizations = get_pending_organizations(Paginated(**request.json))

        return success_response(organizations.model_dump())
    except ValidationError as err:
        logger.error("validation error while parsing paginated pending organizations request", err)
        return bad_request_response(err.errors())
    except Exception as err:
        logger.error(str(err))
        return error_response()

@organization.patch('/active/<organization_id>')
@roles_required([Role.ADMIN.name])
def active_organization(organization_id):
    try:
        handle_active_organization(organization_id)

        return no_content_response()
    except ElementNotFoundException as err:
        logger.warning(str(err))
        return not_found_response(err.message)
    except Exception as err:
        logger.error(str(err))
        return error_response()
