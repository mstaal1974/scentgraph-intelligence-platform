from pydantic import BaseModel, ConfigDict, HttpUrl


class BrandRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    slug: str
    country: str | None = None
    website: HttpUrl | None = None
    verified: bool = False
    review_status: str
