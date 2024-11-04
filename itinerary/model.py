from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, model_validator
from typing_extensions import Self

from common.json_encoders import PyObjectId
from common.model import Paginated, Coordinates
from common.utils import is_valid_enum_name

COLLECTION_NAME = "itineraries"

class CannotUpdateItineraryException(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message

class DateNotValidException(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message

class CityDescriptionNotFoundException(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message

class ItineraryRequestStatus(Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    ERROR = "error"

class ItineraryStatus(Enum):
    PENDING = "pending"
    READY = "ready"
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
    NONE = "none"
    SOLO = "solo"
    COUPLE = "in couple"
    FAMILY = "with family"
    FRIENDS = "with friends"

class Budget(Enum):
    NONE = (-1, -1)
    LOW = (0, 500)
    MEDIUM = (500, 1000)
    HIGH = (1000, 5000)

    @property
    def min(self):
        return self.value[0]

    @property
    def max(self):
        return self.value[1]

class ItinerarySearch(Paginated):
    city: str = ""
    budget: str = Budget.NONE.name
    interested_in: list[str] = []
    travelling_with: str = TravellingWith.NONE.name

    @model_validator(mode='before')
    def check_enums(self) -> Self:
        if "budget" in self and not is_valid_enum_name(Budget, self["budget"]):
            raise ValueError(f'Invalid Budget name: {self["budget"]}')

        if "interested_in" in self:
            for activity in self["interested_in"]:
                if not is_valid_enum_name(Activity, activity):
                    raise ValueError(f'Invalid Activity name: {activity}')

        if "travelling_with" in self and not is_valid_enum_name(TravellingWith, self["travelling_with"]):
            raise ValueError(f'Invalid TravellingWith name: {self["travelling_with"]}')

        return self

    @model_validator(mode='after')
    def check_filters(self) -> Self:
        if (
            self.city == "" and
            self.budget == Budget.NONE.name and
            self.travelling_with == TravellingWith.NONE.name and
            self.interested_in == []
        ):
            raise ValueError('No filter provided, at least one should not be empty!')

        return self


class DuplicateRequest(BaseModel):
    id: PyObjectId

class PublishReqeust(BaseModel):
    id: PyObjectId
    is_public: bool

class ShareWithRequest(BaseModel):
    id: PyObjectId
    users: list[str]

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

class ItineraryBaseModel(BaseModel):
    @model_validator(mode='before')
    def check_enums(self) -> Self:
        if not is_valid_enum_name(Budget, self["budget"]):
            raise ValueError(f'Invalid Budget name: {self["budget"]}')

        if not is_valid_enum_name(TravellingWith, self["travelling_with"]):
            raise ValueError(f'Invalid TravellingWith name: {self["travelling_with"]}')

        for activity in self["interested_in"]:
            if not is_valid_enum_name(Activity, activity):
                raise ValueError(f'Invalid Activity name: {activity}')

        return self

    @model_validator(mode='after')
    def check_dates(self) -> Self:
        start_date = self.start_date
        end_date = self.end_date

        # Check that end_date is greater than or equal to start_date
        if end_date < start_date:
            raise ValueError('end_date must be greater than or equal to start_date')

        return self

class UpdateItineraryRequest(ItineraryBaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    city: str
    start_date: datetime
    end_date: datetime
    budget: str
    travelling_with: str
    accessibility: bool
    interested_in: list[str]
    user_id: PyObjectId
    details: list[AssistantItinerary]
    shared_with: list[str]
    status: str
    docs_notification: bool
    reminder_notification: bool
    is_public: bool

class ItineraryRequest(ItineraryBaseModel):
    city: str
    start_date: datetime
    end_date: datetime
    budget: str
    travelling_with: str
    accessibility: bool
    interested_in: list[str]
    user_id: PyObjectId
    status: ItineraryRequestStatus = ItineraryRequestStatus.PENDING.name
    details: list[AssistantItinerary] = []

class Itinerary(ItineraryBaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    city: str
    start_date: datetime
    end_date: datetime
    budget: str
    travelling_with: str
    accessibility: bool
    interested_in: list[str]
    user_id: PyObjectId
    details: list[AssistantItinerary] = []
    shared_with: list[str] = []
    status: str = ItineraryStatus.PENDING.name
    docs_notification: bool = False
    reminder_notification: bool = False
    is_public: bool = False
    created_at: Optional[datetime] = None
    update_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None

    @staticmethod
    def from_document(itinerary: dict):
        return Itinerary(
            city=itinerary["city"],
            start_date=itinerary["start_date"],
            end_date=itinerary["end_date"],
            budget=itinerary["budget"],
            travelling_with=itinerary["travelling_with"],
            accessibility=itinerary["accessibility"],
            interested_in=itinerary["interested_in"],
            details=itinerary["details"],
            user_id=itinerary["user_id"]
        )

    def update_by(self, update_itinerary_req: UpdateItineraryRequest):
        self.city = update_itinerary_req.city
        self.start_date = update_itinerary_req.start_date
        self.end_date = update_itinerary_req.end_date
        self.budget = update_itinerary_req.budget
        self.travelling_with = update_itinerary_req.travelling_with
        self.accessibility = update_itinerary_req.accessibility
        self.interested_in = update_itinerary_req.interested_in
        self.details = update_itinerary_req.details
        self.user_id = update_itinerary_req.user_id

class ItineraryMeta(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    itinerary_id: PyObjectId
    duplicated_by: list[str] = []
    saved_by: list[str] = []
    views: int = 0