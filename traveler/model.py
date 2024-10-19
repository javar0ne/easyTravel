from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from common.json_encoders import PyObjectId

COLLECTION_NAME = "travelers"

class TravelerModel(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    phone_number: str
    currency: str
    name: str
    surname: str
    birth_date: datetime
    interested_in: list[int]
    user_id: Optional[str]

class TravelerCreateModel(BaseModel):
    email: str
    password: str
    phone_number: str
    currency: str
    name: str
    surname: str
    birth_date: datetime
    interested_in: list[int]
    user_id: Optional[str] = None

class TravelerUpdateModel(BaseModel):
    phone_number: str
    currency: str
    name: str
    surname: str
    birth_date: datetime
    interested_in: list[int]
    user_id: str
