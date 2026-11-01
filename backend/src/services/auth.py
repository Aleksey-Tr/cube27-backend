import hashlib
import hmac
import secrets
import time
from datetime import datetime, timedelta, timezone
from typing import Any
from fastapi import HTTPException, Response, status
import jwt

from config import settings
from database import get_session
from orm.user_orm import UserORM
from repositories.companies_repo import CompaniesRepository
from repositories.users_repo import UsersRepository
from roles import LANDLORD_ROLES, ROLE_PERMISSIONS, UserRole
from schemas.user_schemas import (
    UserCreateRequest,
    UserLoginRequest,
    UserRegisterRequest,
    UserUpdateRequest,
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
    expire_delta = (
        expires_delta
        if expires_delta is not None
        else timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    expire = datetime.now(timezone.utc) + expire_delta
    to_encode.update({"exp": int(expire.timestamp()), "iat": int(time.time())})

    return jwt.encode(
        to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )


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
    """Сервис аутентификации, регистрации и управления пользователями/компаниями."""

    @classmethod
    async def register_by_user(
        cls, register_data: UserRegisterRequest
    ) -> UserORM:
        """Самостоятельная регистрация компании-арендатора (подача заявки).

        1. Проверяет, нет ли уже пользователя с таким email.
        2. Проверяет, нет ли уже компании с таким ИНН.
        3. Если таких пользователя и компании нет — создаются компания и пользователь:
           - роль пользователя: 'company'
           - статус пользователя: is_active = False
        """
        async with get_session() as session:
            users_repo = UsersRepository(session)
            companies_repo = CompaniesRepository(session)

            # 1. Проверяем email пользователя
            existing_user = await users_repo.get_by_email(register_data.email)
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Пользователь с таким email уже зарегистрирован",
                )

            # 2. Проверяем ИНН компании
            existing_company = await companies_repo.get_by_inn(register_data.company_inn)
            if existing_company:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Компания с таким ИНН уже зарегистрирована",
                )

            # 3. Создаем компанию
            company = await companies_repo.create(
                name=register_data.company_name.strip(),
                inn=register_data.company_inn.strip(),
                address=register_data.company_address.strip()
            )

            # 4. Создаем пользователя-представителя со статусом is_active=False и ролью company
            password_hash = hash_password(register_data.password)
            user = await users_repo.create_user(
                email=register_data.email.strip(),
                password_hash=password_hash,
                first_name=register_data.first_name.strip(),
                last_name=register_data.last_name.strip(),
                role=UserRole.COMPANY.value,
                company_id=company.id,
                phone=register_data.phone.strip(),
                is_active=False,
            )
            await session.commit()
            return await users_repo.get_by_id_with_role(user.id)

    @classmethod
    async def register_by_admin(
        cls, creator: UserORM, user_data: UserCreateRequest
    ) -> UserORM:
        """Создание пользователя арендодателем (owner или admin).

        При создании пользователю сразу устанавливается is_active=True.
        Если создается роль 'company', создается соответствующая компания в БД.
        """
        creator_role = creator.role.lower() if creator.role else ""
        target_role = user_data.role.lower().strip()

        allowed_targets = ROLE_PERMISSIONS.get(creator_role, set())
        if target_role not in allowed_targets:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Пользователь с ролью '{creator_role}' не может создавать пользователей с ролью '{target_role}'",
            )

        valid_roles = {r.value for r in UserRole}
        if target_role not in valid_roles:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Роль '{target_role}' не существует",
            )

        async with get_session() as session:
            users_repo = UsersRepository(session)
            companies_repo = CompaniesRepository(session)

            # Проверка уникальности email
            existing_user = await users_repo.get_by_email(user_data.email)
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Пользователь с таким email уже существует",
                )

            company_id = user_data.company_id

            # Если создается компания-арендатор: создаем компанию, если передан inn/name
            if target_role == UserRole.COMPANY.value:
                if not company_id:
                    if not user_data.company_name or not user_data.company_inn:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Для создания компании-арендатора необходимо указать company_name и company_inn (или company_id)",
                        )
                    company = await companies_repo.get_or_create(
                        name=user_data.company_name,
                        inn=user_data.company_inn,
                        address=user_data.company_address,
                    )
                    company_id = company.id
            else:
                # Если это сотрудник компании арендодателя, привязываем к компании арендодателя (если она есть)
                if not company_id and creator.company_id:
                    company_id = creator.company_id

            password_hash = hash_password(user_data.password)
            # При создании арендодателем — is_active=True сразу
            return await users_repo.create_user(
                email=user_data.email,
                password_hash=password_hash,
                first_name=user_data.first_name,
                last_name=user_data.last_name,
                role=target_role,
                company_id=company_id,
                phone=user_data.phone,
                is_active=True,
            )

    @classmethod
    async def login_user(
        cls, login_data: UserLoginRequest
    ) -> tuple[UserORM, str]:
        """Вход пользователя в систему. Возвращает (пользователь, jwt_token)."""
        async with get_session() as session:
            users_repo = UsersRepository(session)

            user = await users_repo.get_by_email(login_data.email)
            if not user or not verify_password(login_data.password, user.password_hash):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Неверный email или пароль",
                )

            if not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Ваша учетная запись ожидает подтверждения администратором или была деактивирована",
                )

            role = user.role
            token = create_access_token(
                data={
                    "sub": str(user.id),
                    "email": user.email,
                    "role": user.role,
                    "role": role,
                    "company_id": user.company_id,
                }
            )
            return user, token

    @classmethod
    async def get_user_by_id(
        cls, current_user: UserORM, user_id: int
    ) -> UserORM:
        """Получение пользователя по его ID."""
        creator_role = current_user.role.lower() if current_user.role else ""
        if creator_role not in LANDLORD_ROLES and current_user.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Недостаточно прав для просмотра профиля другого пользователя",
            )

        async with get_session() as session:
            users_repo = UsersRepository(session)
            user = await users_repo.get_by_id_with_role(user_id)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Пользователь с ID {user_id} не найден",
                )
            return user

    @classmethod
    async def update_user_data(
        cls, creator: UserORM, user_id_to_update: int, update_data: UserUpdateRequest
    ) -> UserORM:
        """Редактирование личных данных пользователя и привязанной компании."""
        creator_role = creator.role.lower() if creator.role else ""
        if creator_role not in LANDLORD_ROLES and creator.id != user_id_to_update:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Недостаточно прав для редактирования данных другого пользователя",
            )

        async with get_session() as session:
            users_repo = UsersRepository(session)
            target_user = await users_repo.get_by_id_with_role(user_id_to_update)
            if not target_user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Пользователь с ID {user_id_to_update} не найден",
                )

            # Обновляем компанию (если есть и переданы параметры)
            if target_user.company:
                if update_data.company_name:
                    target_user.company.name = update_data.company_name.strip()
                if update_data.company_address is not None:
                    target_user.company.address = (
                        update_data.company_address.strip()
                        if update_data.company_address
                        else None
                    )

            # Обновляем поля пользователя
            return await users_repo.update_user(
                user=target_user,
                first_name=update_data.first_name,
                last_name=update_data.last_name,
                phone=update_data.phone,
            )

    @classmethod
    async def update_user_status(
        cls, creator: UserORM, user_id_to_update: int, is_active: bool
    ) -> UserORM:
        """Подтверждение заявки или блокировка (owner или admin)."""
        creator_role = creator.role.lower() if creator.role else ""
        if creator_role not in LANDLORD_ROLES:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Недостаточно прав. Только owner или admin могут изменять статус пользователей",
            )

        if creator.id == user_id_to_update and not is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Нельзя деактивировать самого себя",
            )

        async with get_session() as session:
            users_repo = UsersRepository(session)
            target_user = await users_repo.get_by_id_with_role(user_id_to_update)
            if not target_user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Пользователь с ID {user_id_to_update} не найден",
                )

            target_role = target_user.role.lower() if target_user.role else ""

            # Admin не может менять статус у owner или другого admin
            if creator_role == UserRole.ADMIN.value and target_role in (
                UserRole.OWNER.value,
                UserRole.ADMIN.value,
            ):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Администратор не может менять статус главного владельца (owner) или другого администратора",
                )

            return await users_repo.update_status(target_user, is_active=is_active)

    @classmethod
    async def get_users_list(
        cls,
        creator: UserORM,
        role: str | None = None,
        is_active: bool | None = None,
    ) -> list[UserORM]:
        """Получение списка пользователей/заявок (только owner или admin)."""
        creator_role = creator.role.lower() if creator.role else ""
        if creator_role not in LANDLORD_ROLES:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Недостаточно прав. Доступно только owner или admin",
            )

        async with get_session() as session:
            users_repo = UsersRepository(session)
            return await users_repo.get_all(
                role=role, is_active=is_active
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

            creator_role = creator.role.lower() if creator.role else ""
            target_role = target_user.role.lower() if target_user.role else ""

            allowed_targets = ROLE_PERMISSIONS.get(creator_role, set())
            if target_role not in allowed_targets:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Пользователь с ролью '{creator_role}' не имеет прав на удаление пользователя с ролью '{target_role}'",
                )

            await users_repo.delete_user(target_user)
