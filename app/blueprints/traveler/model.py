from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, model_validator
from typing_extensions import Self

from app.encoders import PyObjectId
from app.models import Activity
from app.utils import is_valid_enum_name


class TravelerBaseModel(BaseModel):
    @model_validator(mode='before')
    def check_enums(self) -> Self:
        for activity in self["interested_in"]:
            if not is_valid_enum_name(Activity, activity):
                raise ValueError(f'Invalid Activity name: {activity}')

        return self

class CreateTravelerRequest(TravelerBaseModel):
    email: str
    password: str
    phone_number: str
    currency: str
    name: str
    surname: str
    birth_date: datetime
    interested_in: list[str]
    user_id: Optional[str] = None

class UpdateTravelerRequest(TravelerBaseModel):
    phone_number: str
    currency: str
    name: str
    surname: str
    birth_date: datetime
    interested_in: list[str]

class Traveler(TravelerBaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    phone_number: str
    currency: str
    name: str
    surname: str
    birth_date: datetime
    interested_in: list[str]
    user_id: str
    created_at: Optional[datetime] = None
    update_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None

    @staticmethod
    def from_create_req(traveler: CreateTravelerRequest):
        return Traveler(
            phone_number=traveler.phone_number,
            currency=traveler.currency,
            name=traveler.name,
            surname=traveler.surname,
            birth_date=traveler.birth_date,
            interested_in=traveler.interested_in,
            user_id=traveler.user_id,
        )

    def update_by(self, update_traveler_req: UpdateTravelerRequest):
        self.phone_number = update_traveler_req.phone_number
        self.currency = update_traveler_req.currency
        self.name = update_traveler_req.name
        self.surname = update_traveler_req.surname
        self.birth_date = update_traveler_req.birth_date
        self.interested_in = update_traveler_req.interested_in