from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PropertyBase(BaseModel):
    title: str = Field(min_length=3, max_length=255)
    description: str = ""
    district: str
    address: str
    type: str = "apartment"
    status: str = "active"
    price: int = Field(gt=0)
    rooms: int = Field(gt=0)
    floor: int = Field(ge=0)
    floors_total: int = Field(gt=0)
    contact_info: str = ""
    amenities: list[str] = Field(default_factory=list)
    images: list[str] = Field(default_factory=list)


class PropertyCreate(PropertyBase):
    owner_tg_id: int | None = None


class PropertyUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    district: str | None = None
    address: str | None = None
    type: str | None = None
    status: str | None = None
    price: int | None = Field(default=None, gt=0)
    rooms: int | None = Field(default=None, gt=0)
    floor: int | None = Field(default=None, ge=0)
    floors_total: int | None = Field(default=None, gt=0)
    contact_info: str | None = None
    amenities: list[str] | None = None
    images: list[str] | None = None
    owner_tg_id: int | None = None


class PropertyOut(PropertyBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    owner_tg_id: int | None = None
    created_at: datetime
    updated_at: datetime


class PropertyListOut(BaseModel):
    items: list[PropertyOut]
    total: int
