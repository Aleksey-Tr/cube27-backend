from fastapi import APIRouter, Depends, Query, status

from dependencies import get_current_user, require_admin
from orm.user_orm import UserORM
from schemas.user_schemas import (
    CompanyBriefResponse,
    UserCreateRequest,
    UserResponse,
    UserStatusUpdateRequest,
    UserUpdateRequest,
)
from services.users_service import UsersService

router = APIRouter(prefix="/users", tags=["Пользователи и управление доступом"])


def _to_user_response(user: UserORM) -> UserResponse:
    return UserResponse(
        id=user.id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        phone=user.phone,
        role=user.role,
        company_id=user.company_id,
        company=(
            CompanyBriefResponse(
                id=user.company.id,
                name=user.company.name,
                inn=user.company.inn,
                address=user.company.address,
            )
            if user.company
            else None
        ),
        is_active=user.is_active,
    )


@router.get(
    "",
    response_model=list[UserResponse],
    summary="Список пользователей (только admin / owner)",
    description=(
        "Возвращает список пользователей системы. "
        "Позволяет фильтровать по роли (например, 'company') и статусу активности is_active "
        "(например, is_active=false для просмотра неподтвержденных заявок компаний-арендаторов)."
    ),
)
async def get_users(
    role: str | None = Query(default=None, description="Фильтр по имени роли (например, 'company')"),
    is_active: bool | None = Query(default=None, description="Фильтр по активности (false — заявки на рассмотрении)"),
    current_user: UserORM = Depends(require_admin),
) -> list[UserResponse]:
    users = await UsersService.get_users_list(
        creator=current_user,
        role=role,
        is_active=is_active,
    )
    return [_to_user_response(u) for u in users]


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Получение пользователя по ID",
    description=(
        "Возвращает детальную информацию о конкретном пользователе, его роли и компании. "
        "Доступно для owner, admin, либо для самого пользователя (просмотр собственного профиля)."
    ),
)
async def get_user_by_id(
    user_id: int,
    current_user: UserORM = Depends(get_current_user),
) -> UserResponse:
    user = await UsersService.get_user_by_id(
        current_user=current_user, user_id=user_id
    )
    return _to_user_response(user)


@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Создание пользователя / компании арендодателем (admin / owner)",
    description=(
        "Создание пользователя согласно иерархии ролей. "
        "При создании арендодателем учетная запись сразу активируется (is_active=True). "
        "При создании компании-арендатора (роль 'company') автоматически создается запись компании в БД. "
        "owner — может создавать любую роль; "
        "admin — может создавать сотрудников компании и компании-арендаторы."
    ),
)
async def create_user(
    user_data: UserCreateRequest,
    current_user: UserORM = Depends(get_current_user),
) -> UserResponse:
    created_user = await UsersService.register_by_admin(
        creator=current_user, user_data=user_data
    )
    return _to_user_response(created_user)


@router.patch(
    "/{user_id}",
    response_model=UserResponse,
    summary="Редактирование данных пользователя (admin / owner или сам пользователь)",
    description="Обновление контактных данных пользователя (имя, фамилия, телефон) и компании.",
)
async def update_user(
    user_id: int,
    update_data: UserUpdateRequest,
    current_user: UserORM = Depends(get_current_user),
) -> UserResponse:
    updated_user = await UsersService.update_user_data(
        creator=current_user,
        user_id_to_update=user_id,
        update_data=update_data,
    )
    return _to_user_response(updated_user)


@router.patch(
    "/{user_id}/status",
    response_model=UserResponse,
    summary="Подтверждение / активация / блокировка пользователя (admin / owner)",
    description=(
        "Изменение статуса is_active пользователя. "
        "Используется для одобрения заявки компании-арендатора (is_active=true) либо для блокировки доступа (is_active=false)."
    ),
)
async def update_user_status(
    user_id: int,
    status_data: UserStatusUpdateRequest,
    current_user: UserORM = Depends(require_admin),
) -> UserResponse:
    updated_user = await UsersService.update_user_status(
        creator=current_user,
        user_id_to_update=user_id,
        is_active=status_data.is_active,
    )
    return _to_user_response(updated_user)


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удаление пользователя (согласно иерархии)",
    description=(
        "Удаление пользователя согласно иерархии ролей: "
        "owner — может удалять пользователей любых ролей; "
        "admin — может удалять сотрудников компании и компании-арендаторы."
    ),
)
async def delete_user(
    user_id: int,
    current_user: UserORM = Depends(get_current_user),
) -> None:
    await UsersService.delete_user_by_creator(
        creator=current_user, user_id_to_delete=user_id
    )
