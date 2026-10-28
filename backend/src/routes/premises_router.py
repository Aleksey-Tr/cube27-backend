from fastapi import APIRouter, Depends, Query, status

from dependencies import require_owner
from orm.user_orm import UserORM
from schemas.premise_schemas import (
    PremiseCreate,
    PremiseResponse,
    PremiseUpdate,
)
from services.premises_service import PremisesService

router = APIRouter(prefix="/premises", tags=["Помещения"])


@router.get(
    "",
    response_model=list[PremiseResponse],
    summary="Получение списка помещений (публичный доступ)",
    description="Возвращает список всех помещений. Доступен всем пользователям без авторизации.",
)
async def get_premises(
    status: str | None = Query(default=None, description="Фильтр по статусу (например, 'Free')"),
    floor: int | None = Query(default=None, description="Фильтр по этажу"),
) -> list[PremiseResponse]:
    return await PremisesService.get_all(status_filter=status, floor=floor)


@router.get(
    "/{premise_id}",
    response_model=PremiseResponse,
    summary="Получение помещения по ID (публичный доступ)",
    description="Возвращает детальную информацию о конкретном помещении. Доступен всем пользователям.",
)
async def get_premise(premise_id: int) -> PremiseResponse:
    return await PremisesService.get_by_id(premise_id=premise_id)


# --- ЗАЩИЩЕННЫЕ ЭНДПОИНТЫ (только для роли 'owner') ---


@router.post(
    "",
    response_model=PremiseResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Создание помещения (только owner)",
    description="Создает новое помещение в системе. Доступно только пользователю с ролью 'owner'.",
)
async def create_premise(
    premise_data: PremiseCreate,
    current_user: UserORM = Depends(require_owner),
) -> PremiseResponse:
    return await PremisesService.create(data=premise_data)


@router.patch(
    "/{premise_id}",
    response_model=PremiseResponse,
    summary="Редактирование помещения (только owner)",
    description="Частично обновляет данные помещения. Доступно только пользователю с ролью 'owner'.",
)
async def update_premise(
    premise_id: int,
    premise_data: PremiseUpdate,
    current_user: UserORM = Depends(require_owner),
) -> PremiseResponse:
    return await PremisesService.update(premise_id=premise_id, data=premise_data)


@router.delete(
    "/{premise_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удаление помещения (только owner)",
    description="Удаляет помещение из системы. Доступно только пользователю с ролью 'owner'.",
)
async def delete_premise(
    premise_id: int,
    current_user: UserORM = Depends(require_owner),
) -> None:
    await PremisesService.delete(premise_id=premise_id)
