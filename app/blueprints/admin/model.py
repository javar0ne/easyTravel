from typing import Optional

from pydantic import BaseModel, Field

from app.encoders import PyObjectId

COLLECTION_NAME = "admin_config"

class Config(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    is_itinerary_active: bool = True

class ItineraryActivationRequest(BaseModel):
    is_itinerary_active: bool