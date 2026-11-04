from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class MeterReadingCreate(BaseModel):
    value: Decimal = Field(
        ..., ge=0, max_digits=12, decimal_places=2,
        description="Показание счётчика", examples=["1234.56"],
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
