from fastapi import APIRouter, Depends, Response

from dependencies import get_current_user
from orm.user_orm import UserORM
from schemas.user_schemas import UserLoginRequest, UserMeResponse, UserResponse
from services.auth import AuthService, delete_auth_cookie, set_auth_cookie

router = APIRouter(prefix="/auth", tags=["Аутентификация"])


@router.get(
    "/me",
    response_model=UserMeResponse,
    summary="Текущий авторизованный пользователь",
    description="Возвращает данные о пользователе, под которым выполнен вход.",
)
async def get_me(current_user: UserORM = Depends(get_current_user)) -> UserMeResponse:
    return UserMeResponse(
        id=current_user.id,
        email=current_user.email,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        role_id=current_user.role_id,
        role_name=current_user.role.name if current_user.role else None,
        company_id=current_user.company_id,
        phone=current_user.phone,
        is_active=current_user.is_active,
    )


@router.post(
    "/login",
    response_model=UserResponse,
    summary="Вход в систему",
    description="Проверяет учетные данные пользователя и записывает JWT-токен в HttpOnly Cookie.",
)
async def login(
    login_data: UserLoginRequest,
    response: Response,
) -> UserResponse:
    user, token = await AuthService.login_user(login_data)
    set_auth_cookie(response=response, token=token)
    return user


@router.post(
    "/logout",
    summary="Выход из системы",
    description="Очищает HttpOnly Cookie с JWT-токеном.",
)
async def logout(response: Response) -> dict[str, str]:
    delete_auth_cookie(response)
    return {"message": "Успешный выход из системы"}
