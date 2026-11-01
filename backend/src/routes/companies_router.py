from fastapi import APIRouter, Depends, Query, status

from dependencies import get_current_user, require_admin_or_owner, require_roles
from orm.user_orm import UserORM
from roles import UserRole
from schemas.company_schemas import (
    CompanyContractBrief,
    CompanyCreate,
    CompanyDetailResponse,
    CompanyPremiseBrief,
    CompanyResponse,
    CompanyUpdate,
)
from schemas.user_schemas import CompanyBriefResponse, UserResponse
from services.companies_service import CompaniesService

router = APIRouter(prefix="/companies", tags=["Компании-арендаторы"])


@router.get(
    "",
    response_model=list[CompanyResponse],
    summary="Список компаний-арендаторов",
    description=(
        "Возвращает список всех зарегистрированных компаний. "
        "Доступно для owner, admin и lease_manager. "
        "Поддерживает поиск по названию компании и ИНН."
    ),
)
async def get_companies(
    search: str | None = Query(default=None, description="Поиск по названию компании или ИНН"),
    current_user: UserORM = Depends(
        require_roles(
            UserRole.OWNER.value,
            UserRole.ADMIN.value,
            UserRole.LEASE_MANAGER.value,
        )
    ),
) -> list[CompanyResponse]:
    return await CompaniesService.get_all(search=search)


@router.get(
    "/{company_id}",
    response_model=CompanyDetailResponse,
    summary="Детальная карточка арендатора",
    description=(
        "Возвращает полную информацию о компании, контактных лицах (пользователях), "
        "договорах и арендуемых помещениях. "
        "Доступно для owner, admin, lease_manager, либо для самого арендатора."
    ),
)
async def get_company_by_id(
    company_id: int,
    current_user: UserORM = Depends(get_current_user),
) -> CompanyDetailResponse:
    company = await CompaniesService.get_by_id(
        current_user=current_user, company_id=company_id
    )

    # Формируем ответ со вложенными пользователями и договорами
    users_resp = [
        UserResponse(
            id=u.id,
            email=u.email,
            first_name=u.first_name,
            last_name=u.last_name,
            phone=u.phone,
            role=u.role,
            company_id=u.company_id,
            company=CompanyBriefResponse(
                id=company.id,
                name=company.name,
                inn=company.inn,
                address=company.address,
            ),
            is_active=u.is_active,
        )
        for u in (company.users or [])
    ]

    contracts_resp = [
        CompanyContractBrief(
            id=c.id,
            contract_number=c.contract_number,
            start_date=c.start_date,
            end_date=c.end_date,
            status=c.status,
            premises=[
                CompanyPremiseBrief(
                    id=p.id,
                    floor=p.floor,
                    room_number=p.room_number,
                    area=float(p.area),
                    price=float(p.price),
                    status=p.status,
                )
                for p in (c.premises or [])
            ],
        )
        for c in (company.contracts or [])
    ]

    return CompanyDetailResponse(
        id=company.id,
        name=company.name,
        inn=company.inn,
        address=company.address,
        created_at=company.created_at,
        users=users_resp,
        contracts=contracts_resp,
    )


@router.post(
    "",
    response_model=CompanyResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Создание компании (admin / owner)",
    description="Создает новую компанию в системе. Доступно только owner или admin.",
)
async def create_company(
    data: CompanyCreate,
    current_user: UserORM = Depends(require_admin_or_owner),
) -> CompanyResponse:
    return await CompaniesService.create(data=data)


@router.patch(
    "/{company_id}",
    response_model=CompanyResponse,
    summary="Редактирование данных компании (admin / owner)",
    description="Обновляет название, ИНН или юридический адрес компании. Доступно owner или admin.",
)
async def update_company(
    company_id: int,
    data: CompanyUpdate,
    current_user: UserORM = Depends(require_admin_or_owner),
) -> CompanyResponse:
    return await CompaniesService.update(company_id=company_id, data=data)


@router.delete(
    "/{company_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удаление компании (admin / owner)",
    description="Удаляет компанию из системы. Каскадно удаляет связанные договоры и пользователей.",
)
async def delete_company(
    company_id: int,
    current_user: UserORM = Depends(require_admin_or_owner),
) -> None:
    await CompaniesService.delete(company_id=company_id)
