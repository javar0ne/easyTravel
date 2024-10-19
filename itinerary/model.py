from pydantic import BaseModel

class CityDescription(BaseModel):
    name: str
    description: str
    lat: float
    lon: float