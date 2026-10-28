from fastapi import APIRouter, Depends, status

from dependencies import get_current_user
from orm.user_orm import UserORM
from schemas.user_schemas import UserCreateRequest, UserResponse
from services.auth import AuthService

router = APIRouter(prefix="/users", tags=["Пользователи"])


@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Создание пользователя",
    description=(
        "Создание пользователя согласно иерархии ролей: "
        "owner — может создавать пользователей с любой ролью; "
        "admin — может создавать company-owner и ниже; "
        "company-owner — создает работников только своей компании (электрик, сантехник)."
    ),
)
async def create_user(
    user_data: UserCreateRequest,
    current_user: UserORM = Depends(get_current_user),
) -> UserResponse:
    return await AuthService.create_user_by_creator(
        creator=current_user, user_data=user_data
    )


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удаление пользователя",
    description=(
        "Удаление пользователя согласно иерархии ролей: "
        "owner — может удалять пользователей любых ролей; "
        "admin — может удалять company-owner и работников; "
        "company-owner — может удалять только работников своей компании."
    ),
)
async def delete_user(
    user_id: int,
    current_user: UserORM = Depends(get_current_user),
) -> None:
    await AuthService.delete_user_by_creator(
        creator=current_user, user_id_to_delete=user_id
    )
