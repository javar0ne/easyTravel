from typing import Optional

from pydantic import BaseModel, Field

from common.json_encoders import PyObjectId
from common.model import Coordinates

COLLECTION_NAME = "organizations"

class Organization(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    phone_number: str
    currency: str
    organization_name: str
    coordinates: Coordinates
    website: str
    status: str
    user_id: str

class OrganizationCreateRequest(BaseModel):
    email: str
    password: str
    phone_number: str
    currency: str
    organization_name: str
    coordinates: Coordinates
    website: str
    status: str
    user_id: str

class OrganizationUpdateRequest(BaseModel):
    email: str
    phone_number: str
    currency: str
    organization_name: str
    coordinates: Coordinates
    website: str
    status: str
    user_id: str
