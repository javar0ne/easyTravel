from pydantic import BaseModel

COLLECTION_NAME = "organizations"

class Organization:
    def __init__(
        self,
        phone_number: str = None,
        currency: str = None,
        organization_name: str = None,
        coordinates: list[str] = None,
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

class OrganizationCreateRequest(BaseModel):
    email: str
    password: str
    phone_number: str
    currency: str
    organization_name: str
    coordinates: list[str]
    website: str
    status: str

class OrganizationUpdateRequest(BaseModel):
    email: str
    phone_number: str
    currency: str
    organization_name: str
    coordinates: list[str]
    website: str
    status: str

class OrganizationResponse(BaseModel):
    _id: str
    email: str
    phone_number: str
    currency: str
    organization_name: str
    coordinates: list[str]
    website: str
    status: str
