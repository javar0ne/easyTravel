from datetime import datetime

from marshmallow import Schema, fields

COLLECTION_NAME = "organizations"

class Organization:
    def __init__(
        self,
        phone_number: str = None,
        currency: str = None,
        organization_name: str = None,
        coordinates: str = None,
        website: str = None,
        status: str = None,
        user_id: str = None,
        _id: str = None
    ):
        self.phone_number = phone_number
        self.currency = currency
        self.organization_name = organization_name
        self.coordinates = coordinates
        self.website = website
        self.status = status
        self.user_id = user_id

    def to_dict(self):
        return {
            'phone_number': self.phone_number,
            'currency': self.currency,
            'organization_name': self.organization_name,
            'coordinates': self.coordinates,
            'website': self.website,
            'status': self.status,
            "user_id": self.user_id
        }

class OrganizationCreateRequest(Schema):
    _id = fields.Str(dump_only=True)
    email = fields.Str(required=True)
    password = fields.Str(required=True)
    phone_number = fields.Str(required=True)
    currency = fields.Str(required=True)
    organization_name = fields.Str(required=True)
    coordinates = fields.Str(required=True)
    website = fields.Str(required=True)
    status = fields.Str(required=True)

class OrganizationUpdateRequest(Schema):
    _id = fields.Str(dump_only=True)
    email = fields.Str(required=True)
    phone_number = fields.Str(required=True)
    currency = fields.Str(required=True)
    organization_name = fields.Str(required=True)
    coordinates = fields.Str(required=True)
    website = fields.Str(required=True)
    status = fields.Str(required=True)

class OrganizationResponse(Schema):
    _id = fields.Str(required=True)
    email = fields.Str(required=True)
    phone_number = fields.Str(required=True)
    currency = fields.Str(required=True)
    organization_name = fields.Str(required=True)
    coordinates = fields.Str(required=True)
    website = fields.Str(required=True)
    status = fields.Str(required=True)
