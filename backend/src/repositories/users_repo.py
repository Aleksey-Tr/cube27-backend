from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from orm.role_orm import RoleORM
from orm.user_orm import UserORM


class UsersRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_email(self, email: str) -> UserORM | None:
        stmt = (
            select(UserORM)
            .options(joinedload(UserORM.role), joinedload(UserORM.company))
            .where(UserORM.email == email.strip().lower())
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_by_id(self, user_id: int) -> UserORM | None:
        return await self.session.get(UserORM, user_id)

    async def get_by_id_with_role(self, user_id: int) -> UserORM | None:
        stmt = (
            select(UserORM)
            .options(joinedload(UserORM.role), joinedload(UserORM.company))
            .where(UserORM.id == user_id)
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_all(
        self,
        role_name: str | None = None,
        is_active: bool | None = None,
        company_id: int | None = None,
    ) -> list[UserORM]:
        stmt = (
            select(UserORM)
            .options(joinedload(UserORM.role), joinedload(UserORM.company))
            .order_by(UserORM.id.desc())
        )

        if role_name:
            stmt = stmt.join(UserORM.role).where(RoleORM.name == role_name.strip())
        if is_active is not None:
            stmt = stmt.where(UserORM.is_active == is_active)
        if company_id is not None:
            stmt = stmt.where(UserORM.company_id == company_id)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create_user(
        self,
        email: str,
        password_hash: str,
        first_name: str,
        last_name: str,
        role_id: int,
        company_id: int | None = None,
        phone: str | None = None,
        is_active: bool = False,
    ) -> UserORM:
        user = UserORM(
            email=email.strip().lower(),
            password_hash=password_hash,
            first_name=first_name.strip(),
            last_name=last_name.strip(),
            role_id=role_id,
            company_id=company_id,
            phone=phone.strip() if phone else None,
            is_active=is_active,
        )
        self.session.add(user)
        await self.session.commit()
        return await self.get_by_id_with_role(user.id)  # type: ignore

    async def update_user(
        self,
        user: UserORM,
        first_name: str | None = None,
        last_name: str | None = None,
        phone: str | None = None,
    ) -> UserORM:
        if first_name is not None:
            user.first_name = first_name.strip()
        if last_name is not None:
            user.last_name = last_name.strip()
        if phone is not None:
            user.phone = phone.strip() if phone else None

        await self.session.commit()
        return await self.get_by_id_with_role(user.id)  # type: ignore

    async def update_status(self, user: UserORM, is_active: bool) -> UserORM:
        user.is_active = is_active
        await self.session.commit()
        return await self.get_by_id_with_role(user.id)  # type: ignore

    async def delete_user(self, user: UserORM) -> None:
        await self.session.delete(user)
        await self.session.commit()
