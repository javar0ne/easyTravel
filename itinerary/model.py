from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, model_validator, field_serializer
from typing_extensions import Self

from common.json_encoders import PyObjectId

COLLECTION_NAME = "itineraries"

class ItineraryRequestStatus(Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    ERROR = "error"

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
    COUPLE = "in couple"
    FAMILY = "with family"
    FRIENDS = "with friends"

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
    start_date: datetime
    end_date: datetime
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
    avg_duration: int

class AssistantItinerary(BaseModel):
    day: int
    title: str
    stages: list[Stage]

class AssistantItineraryResponse(BaseModel):
    itinerary: list[AssistantItinerary]

class CityDescription(BaseModel):
    name: str
    description: str
    lat: float
    lon: float

class ItineraryRequest(BaseModel):
    city: str
    start_date: datetime
    end_date: datetime
    budget: Budget
    travelling_with: TravellingWith
    accessibility: bool
    interested_in: list[Activity]
    status: ItineraryRequestStatus = ItineraryRequestStatus.PENDING
    itinerary: list[AssistantItinerary] = []

    @field_serializer('budget')
    def serialize_budget(self, budget: str):
        return Budget[budget]

    @field_serializer('interested_in')
    def serialize_interested_in(self, interested_in: str):
        return [Activity[activity] for activity in interested_in]

    @field_serializer('travelling_with')
    def serialize_travelling_with(self, travelling_with: str):
        return TravellingWith[travelling_with]

    @model_validator(mode='after')
    def check_dates(self) -> Self:
        start_date = self.start_date
        end_date = self.end_date
        # Check that end_date is greater than or equal to start_date
        if end_date < start_date:
            raise ValueError('end_date must be greater than or equal to start_date')
        return self