from datetime import date, datetime
from pydantic import BaseModel, ConfigDict, Field

from schemas.user_schemas import UserResponse


class CompanyCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255, description="Название компании")
    inn: str = Field(min_length=10, max_length=12, description="ИНН компании (10 или 12 цифр)")
    address: str | None = Field(default=None, description="Юридический адрес")


class CompanyUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=255, description="Название компании")
    inn: str | None = Field(default=None, max_length=12, description="ИНН компании")
    address: str | None = Field(default=None, description="Юридический адрес")


class CompanyResponse(BaseModel):
    id: int
    name: str
    inn: str
    address: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CompanyPremiseBrief(BaseModel):
    id: int
    floor: int
    room_number: str
    area: float
    price: float
    status: str

    model_config = ConfigDict(from_attributes=True)


class CompanyContractBrief(BaseModel):
    id: int
    contract_number: str
    start_date: date
    end_date: date
    status: str
    premises: list[CompanyPremiseBrief] = []

    model_config = ConfigDict(from_attributes=True)


class CompanyDetailResponse(CompanyResponse):
    """Детальная карточка арендатора со списком пользователей и договоров/помещений."""

    users: list[UserResponse] = []
    contracts: list[CompanyContractBrief] = []

    model_config = ConfigDict(from_attributes=True)
