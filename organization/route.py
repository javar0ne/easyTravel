import logging

from flask import request, jsonify, abort
from marshmallow import ValidationError

from organization import organization
from organization.model import OrganizationCreateRequest, OrganizationResponse, OrganizationUpdateRequest
from organization.service import create_organization, get_organization_by_id, update_organization

logger = logging.getLogger(__name__)

@organization.get('/<organization_id>')
def get(organization_id):
    organization = get_organization_by_id(organization_id)

    if organization is None:
        return abort(404, description='no organization found with id {organization_id}')

    return OrganizationResponse().dump(organization), 200

@organization.post('/')
def create():
    try:
        logger.debug("parsing request body to organization..")
        data = request.get_json()
        organization_data = OrganizationCreateRequest().load(data)
    except ValidationError as err:
        logger.error("validation error while parsing organization request", err)
        return jsonify(err.messages), 400

    try:
        inserted_id = create_organization(organization_data)
        return jsonify({"_id": inserted_id}), 200
    except Exception as e:
        logger.error(str(e))
        return abort(500)

@organization.put('/<organization_id>')
def update(organization_id):
    try:
        logger.debug("parsing request body to organization..")
        data = request.get_json()
        organization_data = OrganizationUpdateRequest().load(data)
    except ValidationError as err:
        logger.error("validation error while parsing organization request", err)
        return jsonify(err.messages), 400

    try:
        result = update_organization(organization_id, organization_data)

        if not result:
            return abort(404, description=f'No organization found with id {organization_id}')

        return '', 204
    except Exception as e:
        logger.error(str(e))
        return abort(500)


