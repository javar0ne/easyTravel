from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, model_validator
from typing_extensions import Self

from app.encoders import PyObjectId
from app.models import Activity
from app.utils import is_valid_enum_name


class TravelerSignupConfirmationNotFoundException(Exception):
    def __init__(self):
        super().__init__('Signup confirmation not found!')
        self.message = 'Signup confirmation not found!'

class TravelerBaseModel(BaseModel):
    @model_validator(mode='before')
    def check_enums(self) -> Self:
        if "interested_in" in self:
            for activity in self["interested_in"]:
                if not is_valid_enum_name(Activity, activity):
                    raise ValueError(f'Invalid Activity name: {activity}')

        return self

class CreateTravelerRequest(BaseModel):
    email: str
    password: str
    currency: str
    first_name: str
    last_name: str
    birth_date: datetime
    phone_number: Optional[str] = None
    user_id: Optional[str] = None

class ConfirmTravelerSignupRequest(TravelerBaseModel):
    interested_in: list[str]
    token: str

class UpdateTravelerRequest(TravelerBaseModel):
    currency: str
    first_name: str
    last_name: str
    birth_date: datetime
    interested_in: list[str]
    phone_number: Optional[str] = None

class Traveler(TravelerBaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    currency: str
    first_name: str
    last_name: str
    birth_date: datetime
    user_id: str
    interested_in: Optional[list[str]] = []
    phone_number: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None

    @staticmethod
    def from_create_req(traveler: CreateTravelerRequest):
        return Traveler(
            phone_number=traveler.phone_number,
            currency=traveler.currency,
            first_name=traveler.first_name,
            last_name=traveler.last_name,
            birth_date=traveler.birth_date,
            user_id=traveler.user_id,
        )

    def update_by(self, update_traveler_req: UpdateTravelerRequest):
        self.phone_number = update_traveler_req.phone_number
        self.currency = update_traveler_req.currency
        self.first_name = update_traveler_req.first_name
        self.last_name = update_traveler_req.last_name
        self.birth_date = update_traveler_req.birth_date
        self.interested_in = update_traveler_req.interested_in