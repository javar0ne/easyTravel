import logging

from flask import request
from flask_jwt_extended import get_jwt_identity
from pydantic import ValidationError

from app.blueprints.organization import organization
from app.blueprints.organization.model import CreateOrganizationRequest, UpdateOrganizationRequest
from app.blueprints.organization.service import create_organization, get_organization_by_id, update_organization, \
    get_pending_organizations, handle_active_organization, get_full_organization_by_id
from app.exceptions import ElementAlreadyExistsException, ElementNotFoundException
from app.models import Paginated
from app.response_wrapper import bad_request_response, success_response, conflict_response, not_found_response, \
    error_response, no_content_response
from app.role import roles_required, Role

logger = logging.getLogger(__name__)

@organization.get('')
@roles_required([Role.ORGANIZATION.name])
def get():
    try:
        organization = get_full_organization_by_id(get_jwt_identity())
        return success_response(organization.model_dump())
    except ElementNotFoundException as err:
        logger.warning(str(err))
        return not_found_response(err.message)
    except Exception as e:
        logger.error(str(e))
        return bad_request_response(str(e))

@organization.post('')
def create():
    try:
        logger.debug("parsing request body to organization..")
        organization_create_req = CreateOrganizationRequest(**request.json)

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

@organization.put('')
@roles_required([Role.ORGANIZATION.name])
def update():
    try:
        logger.debug("parsing request body to organization..")
        organization_data = UpdateOrganizationRequest(**request.json)

        update_organization(get_jwt_identity(), organization_data)
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
