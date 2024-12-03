import math
from enum import Enum

from pydantic import BaseModel, Field, computed_field
from typing_extensions import Optional

from app.encoders import PyObjectId


class Collections(Enum):
    ADMIN_CONFIGS = "admin_configs"
    EVENTS = "events"
    IMAGES = "images"
    ITINERARIES = "itineraries"
    ITINERARY_METAS = "itinerary_metas"
    ITINERARY_REQUESTS = "itinerary_requests"
    ORGANIZATIONS = "organizations"
    RESET_TOKENS = "reset_tokens"
    TRAVELER_SIGNUPS = "traveler_signups"
    TRAVELERS = "travelers"
    USERS = "users"

class UnsplashImageUrls(BaseModel):
    raw: Optional[str] = None
    full: Optional[str] = None
    regular: Optional[str] = None
    small: Optional[str] = None
    thumb: Optional[str] = None
    small_s3: Optional[str] = None

class UnsplashImage(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    city: str
    alt: Optional[str] = ""
    urls: UnsplashImageUrls

    @staticmethod
    def from_unsplash(response: dict, city: str):
        return UnsplashImage(city=city, alt=response.get("alt_description"), urls=response.get("urls"))

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
