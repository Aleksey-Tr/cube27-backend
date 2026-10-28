from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from config import settings
from database import get_session
from orm.user_orm import UserORM
from services.auth import decode_access_token


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
            .options(joinedload(UserORM.role))
            .where(UserORM.id == user_id)
        )
        result = await session.execute(stmt)
        user = result.scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Пользователь не найден",
        )

    return user


async def require_owner(current_user: UserORM = Depends(get_current_user)) -> UserORM:
    """Проверяет, что у пользователя роль 'owner' (хозяин)."""
    role_name = current_user.role.name.lower() if current_user.role else ""
    if role_name != "owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав. Действие доступно только пользователям с ролью 'owner'",
        )
    return current_user


async def require_admin_or_owner(
    current_user: UserORM = Depends(get_current_user),
) -> UserORM:
    """Проверяет, что у пользователя роль 'owner' или 'admin'."""
    role_name = current_user.role.name.lower() if current_user.role else ""
    if role_name not in ("owner", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав. Требуется роль 'admin' или 'owner'",
        )
    return current_user


async def require_company_owner_or_above(
    current_user: UserORM = Depends(get_current_user),
) -> UserORM:
    """Проверяет, что у пользователя роль 'company-owner', 'admin' или 'owner'."""
    role_name = current_user.role.name.lower() if current_user.role else ""
    if role_name not in ("owner", "admin", "company-owner"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав. Требуется роль 'company-owner', 'admin' или 'owner'",
        )
    return current_user
