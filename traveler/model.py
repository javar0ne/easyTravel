from cmath import phase
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from common.json_encoders import PyObjectId

COLLECTION_NAME = "travelers"

class TravelerCreateRequest(BaseModel):
    email: str
    password: str
    phone_number: str
    currency: str
    name: str
    surname: str
    birth_date: datetime
    interested_in: list[int]
    user_id: str

class UpdateTravelerRequest(BaseModel):
    phone_number: str
    currency: str
    name: str
    surname: str
    birth_date: datetime
    interested_in: list[int]
    user_id: str

class Traveler(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    phone_number: str
    currency: str
    name: str
    surname: str
    birth_date: datetime
    interested_in: list[int]
    user_id: str
    created_at: Optional[datetime] = None
    update_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None

    @staticmethod
    def from_create_req(traveler: TravelerCreateRequest):
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