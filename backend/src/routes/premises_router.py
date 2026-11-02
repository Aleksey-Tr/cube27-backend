from decimal import Decimal
from fastapi import APIRouter, Depends, Query, status

from dependencies import get_current_user, require_admin, require_roles
from orm.user_orm import UserORM
from roles import UserRole
from schemas.premise_schemas import (
    PremiseAssignRequest,
    PremiseCreate,
    PremiseResponse,
    PremiseUpdate,
    TenantPremiseResponse,
)
from services.premises_service import PremisesService

router = APIRouter(prefix="/premises", tags=["Помещения и аренда"])


@router.get(
    "",
    response_model=list[PremiseResponse],
    summary="Каталог помещений (свободные / витрина по п. 7 ТЗ)",
    description=(
        "Возвращает список всех помещений. Доступен всем пользователям. "
        "Поддерживает фильтры по статусу (например, status='Free' для свободных помещений), "
        "этажу, диапазону площади и цены, а также поиск по номеру комнаты."
    ),
)
async def get_premises(
    status: str | None = Query(default=None, description="Фильтр по статусу: Free, Occupied, Reserved, Maintenance"),
    floor: int | None = Query(default=None, description="Фильтр по этажу"),
    min_area: Decimal | None = Query(default=None, description="Минимальная площадь в кв.м."),
    max_area: Decimal | None = Query(default=None, description="Максимальная площадь в кв.м."),
    min_price: Decimal | None = Query(default=None, description="Минимальная стоимость аренды"),
    max_price: Decimal | None = Query(default=None, description="Максимальная стоимость аренды"),
    search: str | None = Query(default=None, description="Поиск по номеру помещения"),
) -> list[PremiseResponse]:
    return await PremisesService.get_all(
        status_filter=status,
        floor=floor,
        min_area=min_area,
        max_area=max_area,
        min_price=min_price,
        max_price=max_price,
        search=search,
    )


@router.get(
    "/my",
    response_model=list[TenantPremiseResponse],
    summary="Блок «Мои помещения» арендатора (по п. 4.1 ТЗ)",
    description=(
        "Возвращает список помещений, которые арендует текущая компания-арендатор, "
        "включая номер договора аренды, даты начала и окончания, и статус аренды."
    ),
)
async def get_my_premises(
    current_user: UserORM = Depends(get_current_user),
) -> list[TenantPremiseResponse]:
    return await PremisesService.get_my_premises(current_user=current_user)


@router.get(
    "/by-company/{company_id}",
    response_model=list[TenantPremiseResponse],
    summary="Список арендуемых помещений конкретной компании (для сотрудников)",
    description="Возвращает помещения компании. Доступно для owner, admin и lease_manager.",
)
async def get_premises_by_company(
    company_id: int,
    current_user: UserORM = Depends(
        require_roles(
            UserRole.OWNER.value,
            UserRole.ADMIN.value,
            UserRole.LEASE_MANAGER.value,
        )
    ),
) -> list[TenantPremiseResponse]:
    return await PremisesService.get_premises_by_company_id(company_id=company_id)


@router.get(
    "/{premise_id}",
    response_model=PremiseResponse,
    summary="Получение помещения по ID",
    description="Возвращает детальную информацию о конкретном помещении.",
)
async def get_premise(premise_id: int) -> PremiseResponse:
    return await PremisesService.get_by_id(premise_id=premise_id)


# --- ЗАЩИЩЕННЫЕ ЭНДПОИНТЫ УПРАВЛЕНИЯ (owner и admin) ---


@router.post(
    "",
    response_model=PremiseResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Создание помещения (admin / owner)",
    description="Создает новое помещение в системе. Доступно для owner и admin.",
)
async def create_premise(
    premise_data: PremiseCreate,
    current_user: UserORM = Depends(require_admin),
) -> PremiseResponse:
    return await PremisesService.create(data=premise_data)


@router.patch(
    "/{premise_id}",
    response_model=PremiseResponse,
    summary="Редактирование помещения (admin / owner)",
    description="Частично обновляет данные помещения. Доступно для owner и admin.",
)
async def update_premise(
    premise_id: int,
    premise_data: PremiseUpdate,
    current_user: UserORM = Depends(require_admin),
) -> PremiseResponse:
    return await PremisesService.update(premise_id=premise_id, data=premise_data)


@router.post(
    "/{premise_id}/assign",
    summary="Привязка помещения к арендатору с договором (admin / owner / lease_manager)",
    description=(
        "Привязывает помещение к компании, создает или привязывает договор аренды "
        "и переводит помещение в статус 'Occupied' (занято)."
    ),
)
async def assign_premise(
    premise_id: int,
    assign_data: PremiseAssignRequest,
    current_user: UserORM = Depends(
        require_roles(
            UserRole.OWNER.value,
            UserRole.ADMIN.value,
            UserRole.LEASE_MANAGER.value,
        )
    ),
) -> dict[str, str]:
    contract = await PremisesService.assign(premise_id=premise_id, data=assign_data)
    return {
        "message": f"Помещение успешно привязано к компании (договор {contract.contract_number})",
        "contract_number": contract.contract_number,
        "contract_status": contract.status,
    }


@router.delete(
    "/{premise_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удаление помещения (admin / owner)",
    description="Удаляет помещение из системы. Доступно для owner и admin.",
)
async def delete_premise(
    premise_id: int,
    current_user: UserORM = Depends(require_admin),
) -> None:
    await PremisesService.delete(premise_id=premise_id)
