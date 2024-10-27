import logging

from flask import request, jsonify, abort
from pydantic import ValidationError

from common.exception import ElementAlreadyExistsException, ElementNotFoundException
from common.response_wrapper import bad_request_response, success_response, conflict_response, not_found_response, \
    error_response, no_content_response
from organization import organization
from organization.model import OrganizationCreateModel, OrganizationResponse, OrganizationUpdateModel
from organization.service import create_organization, get_organization_by_id, update_organization

logger = logging.getLogger(__name__)

@organization.get('/<organization_id>')
def get(organization_id):
    try:
        organization_document = get_organization_by_id(organization_id)
        return OrganizationResponse(**organization_document).model_dump(), 200
    except Exception as e:
        logger.error(str(e))
        return bad_request_response(str(e))
@organization.post('/')
def create():
    try:
        logger.debug("parsing request body to organization..")
        organization_data = OrganizationCreateModel(**request.json)

        inserted_id = create_organization(organization_data)
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
        organization_data = OrganizationUpdateModel(**request.json)
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


