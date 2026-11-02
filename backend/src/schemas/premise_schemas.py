from datetime import date
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field


class PremiseCreate(BaseModel):
    floor: int = Field(..., description="Этаж, на котором расположено помещение")
    room_number: str = Field(..., max_length=50, description="Номер или название помещения")
    area: Decimal = Field(..., gt=0, decimal_places=2, description="Площадь в кв.м.")
    price: Decimal = Field(..., gt=0, decimal_places=2, description="Базовая стоимость аренды в месяц (руб.)")
    status: str = Field(
        default="Free",
        description="Статус доступности: Free (свободно), Occupied (занято), Reserved (забронировано), Maintenance (на обслуживании/ремонте)",
    )


class PremiseUpdate(BaseModel):
    floor: int | None = Field(default=None, description="Этаж")
    room_number: str | None = Field(default=None, max_length=50, description="Номер помещения")
    area: Decimal | None = Field(default=None, gt=0, decimal_places=2, description="Площадь в кв.м.")
    price: Decimal | None = Field(default=None, gt=0, decimal_places=2, description="Стоимость аренды в месяц")
    status: str | None = Field(default=None, description="Статус доступности (Free, Occupied, Reserved, Maintenance)")


class PremiseResponse(PremiseCreate):
    id: int
    status: str

    model_config = ConfigDict(from_attributes=True)


class TenantPremiseResponse(BaseModel):
    """Схема для раздела «Мои помещения» личного кабинета арендатора (по п. 4.1 ТЗ)."""

    id: int
    room_number: str
    floor: int
    area: Decimal
    price: Decimal
    status: str
    contract_id: int | None = None
    contract_number: str | None = None
    contract_status: str | None = None
    start_date: date | None = None
    end_date: date | None = None

    model_config = ConfigDict(from_attributes=True)


class PremiseAssignRequest(BaseModel):
    """Схема привязки помещения к арендатору с оформлением договора аренды."""

    company_id: int = Field(..., description="ID компании-арендатора")
    contract_number: str = Field(..., max_length=100, description="Номер договора аренды (например, №15/2026)")
    start_date: date = Field(..., description="Дата заключения/начала договора")
    end_date: date = Field(..., description="Дата окончания действия договора")
