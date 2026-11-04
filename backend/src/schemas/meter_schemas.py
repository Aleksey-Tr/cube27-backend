from enum import Enum
from pydantic import BaseModel, ConfigDict, Field, field_validator


class MeterType(str, Enum):
    """Основные типы счетчиков."""

    ELECTRICITY = "электричество"
    WATER = "водоснабжение"

class MeterCreate(BaseModel):
    """Схема создания счетчика."""

    meter_type: MeterType = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Тип счетчика (например, 'электричество', 'водоснабжение')",
        examples=["электричество", "водоснабжение"],
    )
    serial_number: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Заводской серийный номер прибора учета",
        examples=["EL-101-789456", "WTR-101-112233"],
    )

class MeterUpdate(BaseModel):
    """Частичное обновление счетчика без переноса в другое помещение."""

    meter_type: MeterType | None = Field(default=None, description="Тип счетчика")
    serial_number: str | None = Field(
        default=None, min_length=1, max_length=100, description="Заводской серийный номер"
    )

    @field_validator("meter_type", "serial_number", mode="before")
    @classmethod
    def validate_update_value(cls, value):
        if value is None:
            raise ValueError("Значение не может быть null")
        return value.strip() if isinstance(value, str) else value


class MeterResponse(BaseModel):
    """Схема ответа со счетчиком."""

    id: int
    premise_id: int
    meter_type: str
    serial_number: str

    model_config = ConfigDict(from_attributes=True)
