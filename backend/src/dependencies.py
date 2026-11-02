from collections.abc import Callable
from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from config import settings
from database import get_session
from orm.user_orm import UserORM
from roles import LANDLORD_ROLES, STAFF_ROLES, UserRole
from services.users_service import decode_access_token


async def get_current_user(request: Request) -> UserORM:
    """Извлекает и валидирует текущего пользователя из HttpOnly Cookie или Bearer-токена."""
    token = request.cookies.get(settings.COOKIE_KEY)

    # Запасной вариант: заголовок Authorization: Bearer <token>
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Требуется авторизация",
        )

    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Недействительный или истекший токен",
        )

    user_id = int(payload["sub"])
    async with get_session() as session:
        stmt = (
            select(UserORM)
            .options(joinedload(UserORM.company))
            .where(UserORM.id == user_id)
        )
        result = await session.execute(stmt)
        user = result.scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Пользователь не найден",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Пользователь заблокирован или деактивирован",
        )

    return user

def require_roles(*allowed_roles: str) -> Callable:
    """Фабрика зависимости для проверки наличия у пользователя одной из разрешенных ролей."""

    async def role_checker(
        current_user: UserORM = Depends(get_current_user),
    ) -> UserORM:
        user_role = current_user.role.lower() if current_user.role else ""
        normalized_allowed = {r.lower() for r in allowed_roles}
        if user_role not in normalized_allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Недостаточно прав. Требуется одна из ролей: {', '.join(allowed_roles)}",
            )
        return current_user

    return role_checker


async def require_owner(
    current_user: UserORM = Depends(get_current_user),
) -> UserORM:
    """Проверяет, что у пользователя роль 'owner' (главный владелец)."""
    user_role = current_user.role.lower() if current_user.role else ""
    if user_role != UserRole.OWNER.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав. Действие доступно только роли 'owner'",
        )
    return current_user


async def require_admin(
    current_user: UserORM = Depends(get_current_user),
) -> UserORM:
    """Проверяет, что у пользователя роль 'owner' или 'admin'."""
    user_role = current_user.role.lower() if current_user.role else ""
    if user_role not in LANDLORD_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав. Требуется роль 'admin' или 'owner'",
        )
    return current_user

async def require_company(
    current_user: UserORM = Depends(get_current_user),
) -> UserORM:
    """Проверяет, что текущий пользователь является компанией-арендатором."""
    user_role = current_user.role.lower() if current_user.role else ""
    if user_role not in (UserRole.COMPANY.value, UserRole.OWNER.value, UserRole.ADMIN.value):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав. Раздел предназначен для арендаторов (компаний)",
        )
    return current_user
