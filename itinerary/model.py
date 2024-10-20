from datetime import date
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from common.json_encoders import PyObjectId


class ItineraryStatus(Enum):
    PENDING = "pending"
    STARTED = "started"
    COMPLETED = "completed"

class Activity(Enum):
    BEACH = "beaches"
    CITY_SIGHTSEEING = "city sightseeing"
    OUTDOOR_ADVENTURES = "outdoor adventures"
    FESTIVAL = "festival"
    FOOD_EXPLORATION = "food exploration"
    NIGHTLIFE = "nightlife"
    SHOPPING = "shopping"
    SPA_WELLNESS = "spa wellness"

class TravellingWith(Enum):
    SOLO = "solo"
    COUPLE = "couple"
    FAMILY = "family"
    FRIENDS = "friends"

class Budget(Enum):
    LOW = (0, 500)
    MEDIUM = (500, 1000)
    HIGH = (1000, 5000)

    @property
    def min(self):
        return self.value[0]

    @property
    def max(self):
        return self.value[1]

class Itinerary(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    city: str
    start_date: date
    end_date: date
    budget: Budget
    travelling_with: TravellingWith
    accessibility: bool
    interested_in: list[Activity]
    shared_with: list[str]
    status: ItineraryStatus
    docs_notification: bool
    reminder_notification: bool
    is_public: bool

class Coordinates(BaseModel):
    lat: float
    lng: float

class Stage(BaseModel):
    period: str
    title: str
    description: str
    cost: str
    distance_from_center: float
    accessible: bool
    coordinates: Coordinates
    avg_duration: float

class AssistantItinerary(BaseModel):
    day: int
    title: str
    stages: list[Stage]

class CityDescription(BaseModel):
    name: str
    description: str
    lat: float
    lon: float