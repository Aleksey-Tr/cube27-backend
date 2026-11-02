from fastapi import APIRouter, Depends, Path, status

from dependencies import require_roles
from orm.user_orm import UserORM
from roles import UserRole
from schemas.meter_schemas import MeterCreate, MeterResponse
from services.meters_service import MetersService

router = APIRouter(tags=["Счетчики"])


@router.post(
    "/premises/{id}/meters",
    response_model=MeterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Создание счетчика для помещения",
    description=(
        "Создает новый прибор учета (счетчик) для указанного помещения. "
        "Доступно для owner и admin (любые типы счетчиков), "
        "chief_power_engineer (только счетчики электричества), "
        "chief_emo (только счетчики водоснабжения)."
    ),
)
async def create_meter(
    id: int = Path(..., description="ID помещения"),
    meter_data: MeterCreate = ...,
    current_user: UserORM = Depends(require_roles(UserRole.OWNER.value,
                                                  UserRole.ADMIN.value,
                                                  UserRole.CHIEF_POWER_ENGINEER.value,
                                                  UserRole.CHIEF_EMO.value,))) -> MeterResponse:
    return await MetersService.create_meter(
        premise_id=id,
        data=meter_data,
        current_user=current_user,
    )
