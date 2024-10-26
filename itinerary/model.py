from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, model_validator
from typing_extensions import Self

from common.json_encoders import PyObjectId
from common.utils import is_valid_enum_name

COLLECTION_NAME = "itineraries"

class IsPublicRequest(BaseModel):
    id: PyObjectId
    is_public: bool

class ShareWithRequest(BaseModel):
    id: PyObjectId
    users: list[str]

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
    budget: str
    travelling_with: str
    accessibility: bool
    interested_in: list[str]
    user_id: str
    status: ItineraryRequestStatus = ItineraryRequestStatus.PENDING.name
    details: list[AssistantItinerary] = []

    @model_validator(mode='before')
    def check_enums(self) -> Self:
        if not is_valid_enum_name(Budget, self["budget"]):
            raise ValueError(f'Invalid Budget name: {self["budget"]}')

        if not is_valid_enum_name(TravellingWith, self["travelling_with"]):
            raise ValueError(f'Invalid TravellingWith name: {self["travelling_with"]}')

        for activity in self["interested_in"]:
            if not is_valid_enum_name(Activity, activity):
                raise ValueError(f'Invalid budget name: {activity}')

        return self

    @model_validator(mode='after')
    def check_dates(self) -> Self:
        start_date = self.start_date
        end_date = self.end_date

        # Check that end_date is greater than or equal to start_date
        if end_date < start_date:
            raise ValueError('end_date must be greater than or equal to start_date')

        # check that end_date is grater or equal to end_date
        if start_date.astimezone(timezone.utc) < datetime.today().astimezone(timezone.utc):
            raise ValueError('start_date must be greater than or equal to today')

        return self

class Itinerary(ItineraryRequest):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    shared_with: list[str] = []
    status: ItineraryStatus = ItineraryStatus.PENDING.name
    docs_notification: bool = False
    reminder_notification: bool = False
    is_public: bool = False

    @staticmethod
    def from_request_document(itinerary_request: dict):
        return Itinerary(
            city=itinerary_request["city"],
            start_date=itinerary_request["start_date"],
            end_date=itinerary_request["end_date"],
            budget=itinerary_request["budget"],
            travelling_with=itinerary_request["travelling_with"],
            accessibility=itinerary_request["accessibility"],
            interested_in=itinerary_request["interested_in"],
            details=itinerary_request["details"],
            user_id=itinerary_request["user_id"]
        )
