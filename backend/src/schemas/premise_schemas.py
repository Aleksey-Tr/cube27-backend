from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field


class PremiseCreate(BaseModel):
    floor: int = Field(..., description="Этаж")
    room_number: str = Field(..., max_length=50, description="Номер помещения")
    area: Decimal = Field(..., gt=0, decimal_places=2, description="Площадь в кв.м.")
    price: Decimal = Field(..., gt=0, decimal_places=2, description="Стоимость аренды в месяц")
    status: str = Field(default="Free", max_length=50, description="Статус доступности помещения")


class PremiseUpdate(BaseModel):
    floor: int | None = Field(default=None, description="Этаж")
    room_number: str | None = Field(default=None, max_length=50, description="Номер помещения")
    area: Decimal | None = Field(default=None, gt=0, decimal_places=2, description="Площадь в кв.м.")
    price: Decimal | None = Field(default=None, gt=0, decimal_places=2, description="Стоимость аренды в месяц")
    status: str | None = Field(default=None, max_length=50, description="Статус доступности помещения")


class PremiseResponse(PremiseCreate):
    id: int
    status: str

    model_config = ConfigDict(from_attributes=True)
