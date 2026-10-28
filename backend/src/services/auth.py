import hashlib
import hmac
import secrets
import time
from datetime import datetime, timedelta, timezone
from typing import Any
from fastapi import HTTPException, Response, status
import jwt

from sqlalchemy import func, select

from config import settings
from database import get_session
from orm.role_orm import RoleORM
from orm.user_orm import UserORM
from repositories.users_repo import UsersRepository
from roles import ROLE_PERMISSIONS, UserRole
from schemas.user_schemas import (
    UserCreateRequest,
    UserLoginRequest
)


def hash_password(password: str) -> str:
    """Хеширование пароля через PBKDF2-HMAC-SHA256 с солью."""
    salt = secrets.token_bytes(16)
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
    return f"pbkdf2:sha256:100000${salt.hex()}${key.hex()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверка пароля против сохраненного хеша."""
    if plain_password == hashed_password:
        return True
    try:
        parts = hashed_password.split("$")
        if len(parts) != 3:
            return False
        _algorithm, salt_hex, hash_hex = parts
        salt = bytes.fromhex(salt_hex)
        expected_hash = bytes.fromhex(hash_hex)
        actual_hash = hashlib.pbkdf2_hmac(
            "sha256", plain_password.encode("utf-8"), salt, 100_000
        )
        return hmac.compare_digest(actual_hash, expected_hash)
    except Exception:
        return False


def create_access_token(
    data: dict[str, Any], expires_delta: timedelta | None = None
) -> str:
    """Генерация JWT-токена."""
    to_encode = data.copy()
    expire_delta = (expires_delta
        if expires_delta is not None
        else timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    expire = datetime.now(timezone.utc) + expire_delta
    to_encode.update({"exp": int(expire.timestamp()), "iat": int(time.time())})

    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any] | None:
    """Декодирование и верификация JWT токена через PyJWT."""
    try:
        return jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
    except jwt.PyJWTError:
        return None


def set_auth_cookie(response: Response, token: str) -> None:
    """Запись JWT токена в HTTP-only Cookie."""
    max_age_seconds = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    response.set_cookie(
        key=settings.COOKIE_KEY,
        value=token,
        max_age=max_age_seconds,
        expires=max_age_seconds,
        httponly=True,
        samesite="lax",
        secure=settings.COOKIE_SECURE,
        path="/",
    )


def delete_auth_cookie(response: Response) -> None:
    """Удаление авторизационной куки."""
    response.delete_cookie(
        key=settings.COOKIE_KEY,
        httponly=True,
        samesite="lax",
        path="/",
    )


class AuthService:
    """Сервис аутентификации.
    """
    

    @classmethod
    async def login_user(
        cls, login_data: UserLoginRequest
    ) -> tuple[UserORM, str]:
        """Вход пользователя. Возвращает (пользователь, jwt_token)."""
        async with get_session() as session:
            users_repo = UsersRepository(session)

            user = await users_repo.get_by_email(login_data.email)
            if not user or not verify_password(login_data.password, user.password_hash):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Неверный email или пароль",
                )

            token = create_access_token(
                data={
                    "sub": str(user.id),
                    "email": user.email,
                    "role_id": user.role_id,
                }
            )
            return user, token

    @classmethod
    async def create_user_by_creator(
        cls, creator: UserORM, user_data: UserCreateRequest
    ) -> UserORM:
        """Создание пользователя с контролем прав по иерархии ролей."""
        creator_role = creator.role.name.lower() if creator.role else ""
        target_role = user_data.role_name.lower().strip()

        allowed_targets = ROLE_PERMISSIONS.get(creator_role, set())
        if target_role not in allowed_targets:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Пользователь с ролью '{creator_role}' не может создавать пользователей с ролью '{target_role}'",
            )

        # company-owner может создавать работников только для своей компании
        company_id = user_data.company_id
        if creator_role == UserRole.COMPANY_OWNER.value:
            if not creator.company_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="У текущего company-owner не указан company_id",
                )
            company_id = creator.company_id

        async with get_session() as session:
            # Поиск роли в БД
            stmt = select(RoleORM).where(func.lower(RoleORM.name) == target_role)
            role = (await session.execute(stmt)).scalars().first()
            if not role:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Роль '{target_role}' не найдена в базе данных",
                )

            users_repo = UsersRepository(session)
            existing_user = await users_repo.get_by_email(user_data.email)
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Пользователь с таким email уже существует",
                )

            password_hash = hash_password(user_data.password)
            return await users_repo.create_user(
                email=user_data.email,
                password_hash=password_hash,
                first_name=user_data.first_name,
                last_name=user_data.last_name,
                role_id=role.id,
                company_id=company_id,
                phone=user_data.phone,
            )

    @classmethod
    async def delete_user_by_creator(
        cls, creator: UserORM, user_id_to_delete: int
    ) -> None:
        """Удаление пользователя с контролем прав по иерархии ролей."""
        if creator.id == user_id_to_delete:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Нельзя удалить самого себя",
            )

        async with get_session() as session:
            users_repo = UsersRepository(session)
            target_user = await users_repo.get_by_id_with_role(user_id_to_delete)
            if not target_user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Пользователь с ID {user_id_to_delete} не найден",
                )

            creator_role = creator.role.name.lower() if creator.role else ""
            target_role = target_user.role.name.lower() if target_user.role else ""

            allowed_targets = ROLE_PERMISSIONS.get(creator_role, set())
            if target_role not in allowed_targets:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Пользователь с ролью '{creator_role}' не имеет прав на удаление пользователя с ролью '{target_role}'",
                )

            # company-owner может удалять работников только своей компании
            if creator_role == UserRole.COMPANY_OWNER.value:
                if target_user.company_id != creator.company_id:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Вы можете удалять только работников своей компании",
                    )

            await users_repo.delete_user(target_user)
