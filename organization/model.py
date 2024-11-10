from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from common.json_encoders import PyObjectId
from common.model import Coordinates

COLLECTION_NAME = "organizations"

class OrganizationStatus(Enum):
    PENDING = "pending"
    ACTIVE = "active"

class OrganizationCreateRequest(BaseModel):
    email: str
    password: str
    phone_number: str
    currency: str
    organization_name: str
    coordinates: Coordinates
    website: str
    status: str = OrganizationStatus.PENDING.name
    user_id: Optional[str] = None

class UpdateOrganizationRequest(BaseModel):
    phone_number: str
    currency: str
    organization_name: str
    coordinates: Coordinates
    website: str

class Organization(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    phone_number: str
    currency: str
    organization_name: str
    coordinates: Coordinates
    website: str
    status: str
    user_id: str
    created_at: Optional[datetime] = None
    update_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None

    def update_by(self, update_organization_req: UpdateOrganizationRequest):
        self.phone_number = update_organization_req.phone_number
        self.currency = update_organization_req.currency
        self.organization_name = update_organization_req.organization_name
        self.coordinates = update_organization_req.coordinates
        self.website = update_organization_req.website

    @staticmethod
    def from_create_req(organization: OrganizationCreateRequest):
        return Organization(
            phone_number=organization.phone_number,
            currency=organization.currency,
            organization_name=organization.organization_name,
            coordinates=organization.coordinates,
            website=organization.website,
            status=OrganizationStatus.PENDING.name,
            user_id=organization.user_id
        )
