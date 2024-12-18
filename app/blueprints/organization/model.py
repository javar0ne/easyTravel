from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from app.blueprints.user.model import User
from app.encoders import PyObjectId
from app.models import Coordinates

COLLECTION_NAME = "organizations"

class OrganizationStatus(Enum):
    PENDING = "pending"
    ACTIVE = "active"

class CreateOrganizationRequest(BaseModel):
    email: str
    password: str
    organization_name: str
    coordinates: Coordinates
    website: Optional[str] = None
    phone_number: Optional[str] = None
    status: str = OrganizationStatus.PENDING.name
    user_id: Optional[str] = None

class UpdateOrganizationRequest(BaseModel):
    email: str
    phone_number: str
    organization_name: str
    coordinates: Coordinates
    website: str

class Organization(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    phone_number: str
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
        self.organization_name = update_organization_req.organization_name
        self.coordinates = update_organization_req.coordinates
        self.website = update_organization_req.website

    @staticmethod
    def from_create_req(organization: CreateOrganizationRequest):
        return Organization(
            phone_number=organization.phone_number,
            organization_name=organization.organization_name,
            coordinates=organization.coordinates,
            website=organization.website,
            status=OrganizationStatus.ACTIVE.name,
            user_id=organization.user_id
        )

class OrganizationFull(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    email: str
    phone_number: str
    organization_name: str
    coordinates: Coordinates
    website: str
    status: str
    user_id: str

    @staticmethod
    def from_sources(organization: Organization, user: User):
        return OrganizationFull(
            id=organization.id,
            email=user.email,
            phone_number=organization.phone_number,
            organization_name=organization.organization_name,
            coordinates=organization.coordinates,
            website=organization.website,
            status=OrganizationStatus.ACTIVE.name,
            user_id=organization.user_id
        )
