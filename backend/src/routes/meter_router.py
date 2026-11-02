from fastapi import APIRouter, Depends, Path, Query, status

from dependencies import get_current_user, require_roles
from orm.user_orm import UserORM
from roles import UserRole
from schemas.meter_schemas import MeterCreate, MeterResponse, MeterType
from services.meters_service import MetersService

router = APIRouter(tags=["Счетчики"])


@router.get(
    "/meters",
    response_model=list[MeterResponse],
    summary="Получение списка всех счетчиков",
    description=(
        "Возвращает список приборов учета (счетчиков). "
        "Администраторам (admin, owner) доступны все счетчики. "
        "Главному энергетику (chief_power_engineer) доступны только счетчики электричества. "
        "Начальнику службы ЭМО (chief_emo) доступны только счетчики водоснабжения."
    ),
)
async def get_all_meters(
    premise_id: int | None = Query(default=None, description="Фильтр по ID помещения"),
    meter_type: MeterType | None = Query(default=None, description="Фильтр по типу счетчика"),
    current_user: UserORM = Depends(
        require_roles(
            UserRole.OWNER.value,
            UserRole.ADMIN.value,
            UserRole.CHIEF_POWER_ENGINEER.value,
            UserRole.CHIEF_EMO.value,
        )
    ),
) -> list[MeterResponse]:
    return await MetersService.get_all_meters(
        current_user=current_user,
        premise_id=premise_id,
        meter_type=meter_type,
    )


@router.get(
    "/premises/{id}/meters",
    response_model=list[MeterResponse],
    summary="Получение счетчиков помещения",
    description=(
        "Возвращает список счетчиков для указанного помещения. "
        "Доступно для администраторов (admin, owner) или арендаторов "
        "(при наличии активного договора аренды на это помещение)."
    ),
)
async def get_premise_meters(
    id: int = Path(..., description="ID помещения"),
    current_user: UserORM = Depends(get_current_user),
) -> list[MeterResponse]:
    return await MetersService.get_premise_meters(
        premise_id=id,
        current_user=current_user,
    )


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
    current_user: UserORM = Depends(
        require_roles(
            UserRole.OWNER.value,
            UserRole.ADMIN.value,
            UserRole.CHIEF_POWER_ENGINEER.value,
            UserRole.CHIEF_EMO.value,
        )
    ),
) -> MeterResponse:
    return await MetersService.create_meter(
        premise_id=id,
        data=meter_data,
        current_user=current_user,
    )
