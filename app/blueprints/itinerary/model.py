import logging
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, model_validator, computed_field
from typing_extensions import Self

from app.encoders import PyObjectId
from app.models import Paginated, Coordinates, Activity, UnsplashImage
from app.utils import is_valid_enum_name, encode_city_name

COLLECTION_NAME = "itineraries"
logger = logging.getLogger(__name__)
class ItineraryGenerationDisabledException(Exception):
    def __init__(self):
        super().__init__("Itinerary generation disabled!")
        self.message = "Itinerary generation disabled!"

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

class DocsNotFoundException(Exception):
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
            if isinstance(self["interested_in"], str):
                if not is_valid_enum_name(Activity, self["interested_in"]):
                    raise ValueError(f'Invalid Activity name: {self["interested_in"]}')
                else:
                    self["interested_in"] = [self["interested_in"]]
            else:
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

    @staticmethod
    def from_request(interested_in: str, city: str, travelling_with: str, budget: str):
        values = {}
        if interested_in and len(interested_in) > 0:
            values["interested_in"] = interested_in
        if city and len(city) > 0:
            values["city"] = city
        if travelling_with and len(travelling_with) > 0:
            values["travelling_with"] = travelling_with
        if budget and len(budget) > 0:
            values["budget"] = budget

        return ItinerarySearch(**values)

class ItinerarySearchResponse(BaseModel):
    id: str
    city: str
    country: str
    description: str
    interested_in: list[str]
    travelling_with: str
    budget: str
    start_date: datetime
    end_date: datetime
    image: UnsplashImage

    @computed_field
    @property
    def duration(self) -> int:
        return (self.end_date - self.start_date).days + 1


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
    accessible: bool
    coordinates: Coordinates
    avg_duration: int

class AssistantItinerary(BaseModel):
    day: int
    title: str
    stages: list[Stage]

class AssistantItineraryResponse(BaseModel):
    itinerary: list[AssistantItinerary]

class CityMetaRequest(BaseModel):
    name: str

class CityDescription(BaseModel):
    name: str
    country: str
    description: str
    lat: float
    lng: float

class AssistantItineraryDocsDetail(BaseModel):
    name: str
    description: str
    done: bool

class AssistantItineraryDocs(BaseModel):
    mandatory: list[AssistantItineraryDocsDetail]
    recommended: list[AssistantItineraryDocsDetail]

class AssistantItineraryDocsResponse(BaseModel):
    docs: list[AssistantItineraryDocs]

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
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    city: str
    start_date: datetime
    end_date: datetime
    budget: str
    travelling_with: str
    accessibility: bool
    interested_in: list[str]
    user_id: Optional[PyObjectId] = None
    status: str = ItineraryRequestStatus.PENDING.name
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
    docs: Optional[AssistantItineraryDocs] = None
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

class SpotlightItinerary(BaseModel):
    id: str
    city: str
    country: str
    description: str
    interested_in: list[str]
    travelling_with: str
    budget: str
    saved_by: int
    shared_with: Optional[list[str]] = []
    start_date: datetime
    end_date: datetime
    image: UnsplashImage

    @computed_field
    @property
    def duration(self) -> int:
        return (self.end_date - self.start_date).days + 1

class UpcomingItinerary(BaseModel):
    id: str
    city: str
    country: str
    description: str
    image: UnsplashImage
    interested_in: list[str]
    travelling_with: str
    budget: str
    start_date: datetime
    end_date: datetime
    shared_with: Optional[list[str]] = []
    is_public: Optional[bool] = False


    @computed_field
    @property
    def duration(self) -> int:
        return (self.end_date - self.start_date).days + 1

    @computed_field
    @property
    def days_from_start(self) -> int:
        return (self.start_date - datetime.now()).days + 1

class PastItinerary(BaseModel):
    id: str
    city: str
    country: str
    image: UnsplashImage
    start_date: datetime
    end_date: datetime
    shared_with: Optional[list[str]] = []

class CityMeta(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    name: str
    key: str
    country: str
    coordinates: Coordinates
    description: str
    image: UnsplashImage

    @staticmethod
    def from_sources(image: UnsplashImage, city_description: CityDescription):
        return CityMeta(
            name=city_description.name,
            key=encode_city_name(city_description.name),
            country=city_description.country,
            coordinates=Coordinates(lat=city_description.lat, lng=city_description.lng),
            description=city_description.description,
            image=image
        )

class ItineraryDetail(BaseModel):
    id: str
    city: str
    country: str
    description: str
    coordinates: Coordinates
    image: UnsplashImage
    start_date: datetime
    end_date: datetime
    budget: str
    travelling_with: str
    accessibility: bool
    interested_in: list[str]
    user_id: str
    details: list[AssistantItinerary] = []
    shared_with: list[str] = []
    status: str
    docs: Optional[AssistantItineraryDocs] = None
    docs_notification: bool = False
    reminder_notification: bool = False
    is_public: bool = False

    @computed_field
    @property
    def budget_min(self) -> int:
        return Budget[self.budget].min

    @computed_field
    @property
    def budget_max(self) -> int:
        return Budget[self.budget].max

    @staticmethod
    def from_sources(itinerary: Itinerary, city_meta: CityMeta):
        return ItineraryDetail(
            id=itinerary.id,
            city=itinerary.city,
            country=city_meta.country,
            description=city_meta.description,
            coordinates=city_meta.coordinates,
            image=city_meta.image,
            start_date=itinerary.start_date,
            end_date=itinerary.end_date,
            budget=itinerary.budget,
            travelling_with=itinerary.travelling_with,
            accessibility=itinerary.accessibility,
            interested_in=itinerary.interested_in,
            user_id=itinerary.user_id,
            details=itinerary.details,
            shared_with=itinerary.shared_with,
            status=itinerary.status,
            docs=itinerary.docs,
            docs_notification=itinerary.docs_notification,
            reminder_notification=itinerary.reminder_notification,
            is_public=itinerary.is_public,
        )

class ItineraryRequestDetail(BaseModel):
    id: str
    city: str
    start_date: datetime
    end_date: datetime
    budget: str
    travelling_with: str
    accessibility: bool
    interested_in: list[str]
    user_id: str
    details: list[AssistantItinerary] = []
    status: str

    @computed_field
    @property
    def budget_min(self) -> int:
        return Budget[self.budget].min

    @computed_field
    @property
    def budget_max(self) -> int:
        return Budget[self.budget].max

    @staticmethod
    def from_req(itinerary_request: ItineraryRequest):
        return ItineraryRequestDetail(
            id=itinerary_request.id,
            city=itinerary_request.city,
            start_date=itinerary_request.start_date,
            end_date=itinerary_request.end_date,
            budget=itinerary_request.budget,
            travelling_with=itinerary_request.travelling_with,
            accessibility=itinerary_request.accessibility,
            interested_in=itinerary_request.interested_in,
            user_id=itinerary_request.user_id,
            details=itinerary_request.details,
            status=itinerary_request.status,
        )

class ItineraryMetaDetail(BaseModel):
    is_owner: bool = False
    has_saved: bool = False