from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from schemas.meter_schemas import MeterResponse


class MeterReadingCreate(BaseModel):
    value: Decimal = Field(
        ..., ge=0, max_digits=12, decimal_places=2,
        description="Показание счётчика", examples=["1234.56"],
    )

    model_config = ConfigDict(extra="forbid")


class MeterReadingStatusUpdate(BaseModel):
    status: Literal["Pending", "Approved", "Rejected"] = Field(
        ..., description="Новый статус показания",
    )

    model_config = ConfigDict(extra="forbid")


class MeterReadingResponse(BaseModel):
    id: int
    meter_id: int
    user_id: int
    value: Decimal
    reading_date: datetime
    status: Literal["Pending", "Approved", "Rejected"]

    model_config = ConfigDict(from_attributes=True)


class ReadingPremiseBriefResponse(BaseModel):
    id: int
    room_number: str
    floor: int

    model_config = ConfigDict(from_attributes=True)


class ReadingMeterResponse(MeterResponse):
    premise: ReadingPremiseBriefResponse


class ReadingUserBriefResponse(BaseModel):
    id: int
    first_name: str
    last_name: str
    role: str

    model_config = ConfigDict(from_attributes=True)


class MeterReadingDetailResponse(MeterReadingResponse):
    user_id: int | None
    meter: ReadingMeterResponse
    user: ReadingUserBriefResponse | None
