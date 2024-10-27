import math

from pydantic import BaseModel, Field, computed_field

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
