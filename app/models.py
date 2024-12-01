import math
from enum import Enum

from pydantic import BaseModel, Field, computed_field


class Collections(Enum):
    ADMIN_CONFIGS = "admin_configs"
    EVENTS = "events"
    ITINERARIES = "itineraries"
    ITINERARY_METAS = "itinerary_metas"
    ITINERARY_REQUESTS = "itinerary_requests"
    ORGANIZATIONS = "organizations"
    RESET_TOKENS = "reset_tokens"
    TRAVELER_SIGNUPS = "traveler_signups"
    TRAVELERS = "travelers"
    USERS = "users"

class Coordinates(BaseModel):
    lat: float
    lng: float

class Activity(Enum):
    BEACH = "beaches"
    CITY_SIGHTSEEING = "city sightseeing"
    OUTDOOR_ADVENTURES = "outdoor adventures"
    FESTIVAL = "festival"
    FOOD_EXPLORATION = "food exploration"
    NIGHTLIFE = "nightlife"
    SHOPPING = "shopping"
    SPA_WELLNESS = "spa wellness"

class Paginated(BaseModel):
    page_number: int = 0
    page_size: int = Field(default=10, le=10)

    @computed_field
    @property
    def elements_to_skip(self) -> int:
        return self.page_size * self.page_number

class PaginatedResponse(BaseModel):
    content: list[dict]
    total_elements: int
    page_size: int
    page_number: int

    @computed_field
    @property
    def total_pages(self) -> int:
        return math.ceil(self.total_elements/self.page_size)
