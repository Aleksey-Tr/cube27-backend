from fastapi import APIRouter, Depends, Response, status

from dependencies import get_current_user
from orm.user_orm import UserORM
from schemas.user_schemas import (
    CompanyBriefResponse,
    UserLoginRequest,
    UserMeResponse,
    UserRegisterRequest,
    UserRegisterResponse,
    UserResponse,
)
from services.users_service import UsersService, delete_auth_cookie, set_auth_cookie

router = APIRouter(prefix="/auth", tags=["Аутентификация и регистрация"])


@router.post(
    "/register",
    response_model=UserRegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Регистрация компании-арендатора (подача заявки)",
    description=(
        "Самостоятельная регистрация компании-арендатора. "
        "Создается запись компании (по названию и ИНН) и учетная запись представителя с ролью 'company'. "
        "По умолчанию аккаунт получает is_active=False. "
        "Вход станет доступен после подтверждения администратором или owner."
    ),
)
async def register(register_data: UserRegisterRequest) -> UserRegisterResponse:
    user = await UsersService.register_by_user(register_data)
    user_response = UserResponse(
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
    return UserRegisterResponse(
        message="Заявка компании успешно отправлена на регистрацию. Ожидайте подтверждения доступа администратором.",
        user=user_response,
    )


@router.post(
    "/login",
    response_model=UserResponse,
    summary="Вход в систему",
    description="Проверяет email и пароль пользователя и записывает JWT-токен в HttpOnly Cookie.",
)
async def login(
    login_data: UserLoginRequest,
    response: Response,
) -> UserResponse:
    user, token = await UsersService.login_user(login_data)
    set_auth_cookie(response=response, token=token)
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


@router.post(
    "/logout",
    summary="Выход из системы",
    description="Очищает HttpOnly Cookie с JWT-токеном.",
)
async def logout(response: Response) -> dict[str, str]:
    delete_auth_cookie(response)
    return {"message": "Успешный выход из системы"}


@router.get(
    "/me",
    response_model=UserMeResponse,
    summary="Текущий авторизованный пользователь",
    description="Возвращает детальные данные о текущем пользователе и его компании.",
)
async def get_me(current_user: UserORM = Depends(get_current_user)) -> UserMeResponse:
    return UserMeResponse(
        id=current_user.id,
        email=current_user.email,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        phone=current_user.phone,
        role=current_user.role,
        company_id=current_user.company_id,
        company=(
            CompanyBriefResponse(
                id=current_user.company.id,
                name=current_user.company.name,
                inn=current_user.company.inn,
                address=current_user.company.address,
            )
            if current_user.company
            else None
        ),
        is_active=current_user.is_active,
    )
