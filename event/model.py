from datetime import datetime
from typing import Optional
from typing_extensions import Self

from pydantic import BaseModel, Field, model_validator

from common.json_encoders import PyObjectId
from common.model import Coordinates
from common.utils import is_valid_enum_name

COLLECTION_NAME = "events"

class EventBaseModel(BaseModel):
    @model_validator(mode='before')
    def check_enums(self) -> Self:
        for activity in self["related_activities"]:
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

class UpdateEventRequest(EventBaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    title: str
    description: str
    cost: str
    avg_duration: int
    accessible: bool
    related_activities: list[str]
    start_date: datetime
    end_date: datetime
    coordinates: Coordinates

class Event(EventBaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    title: str
    description: str
    cost: str
    avg_duration: int
    accessible: bool
    related_activities: list[str]
    start_date: datetime
    end_date: datetime
    coordinates: Coordinates
    organization_id: str
    created_at: Optional[datetime] = None
    update_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None

    def update_by(self, update_event_req: UpdateEventRequest):
        self.title = update_event_req.title
        self.description = update_event_req.description
        self.cost = update_event_req.cost
        self.avg_duration = update_event_req.avg_duration
        self.accessible = update_event_req.accessible
        self.related_activities = update_event_req.related_activities
        self.start_date = update_event_req.start_date
        self.end_date = update_event_req.end_date
        self.coordinates = update_event_req.coordinates