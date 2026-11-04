from fastapi import APIRouter, Depends, Path, status

from dependencies import get_current_user
from orm.user_orm import UserORM
from schemas.meter_reading_schemas import (
    MeterReadingCreate,
    MeterReadingResponse,
    MeterReadingStatusUpdate,
)
from services.meter_readings_service import MeterReadingsService

router = APIRouter(tags=["Показания счётчиков"])


@router.patch(
    "/readings/{id}/status",
    response_model=MeterReadingResponse,
    summary="Изменение статуса показания счётчика",
    description=(
        "Изменяет статус показания на Pending, Approved или Rejected. "
        "owner и admin могут изменять любые показания; chief_power_engineer — "
        "только показания счётчиков электричества, chief_emo — водоснабжения."
    ),
)
async def update_meter_reading_status(
    id: int = Path(..., gt=0, description="ID показания"),
    status_data: MeterReadingStatusUpdate = ...,
    current_user: UserORM = Depends(get_current_user),
) -> MeterReadingResponse:
    return await MeterReadingsService.update_status(
        reading_id=id, data=status_data, current_user=current_user,
    )


@router.post(
    "/meters/{meter_id}/readings",
    response_model=MeterReadingResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Передача показаний счётчика",
    description=(
        "Создаёт показание со статусом Pending. Автор и дата устанавливаются сервером. "
        "owner и admin могут передавать показания любых счётчиков; company — только "
        "для помещения с действующим договором аренды (статус Active и текущая дата "
        "в пределах срока договора). chief_power_engineer — только электричество, "
        "chief_emo — только водоснабжение."
    ),
)
async def create_meter_reading(
    meter_id: int = Path(..., gt=0, description="ID счётчика"),
    reading_data: MeterReadingCreate = ...,
    current_user: UserORM = Depends(get_current_user),
) -> MeterReadingResponse:
    return await MeterReadingsService.create_reading(
        meter_id=meter_id, data=reading_data, current_user=current_user,
    )
