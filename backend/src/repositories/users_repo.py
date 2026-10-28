from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from orm.user_orm import UserORM


class UsersRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_email(self, email: str) -> UserORM | None:
        stmt = select(UserORM).where(UserORM.email == email)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_by_id(self, user_id: int) -> UserORM | None:
        return await self.session.get(UserORM, user_id)

    async def get_by_id_with_role(self, user_id: int) -> UserORM | None:
        stmt = (
            select(UserORM)
            .options(joinedload(UserORM.role))
            .where(UserORM.id == user_id)
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

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
            email=email,
            password_hash=password_hash,
            first_name=first_name,
            last_name=last_name,
            role_id=role_id,
            company_id=company_id,
            phone=phone,
            is_active=is_active,
        )
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def delete_user(self, user: UserORM) -> None:
        await self.session.delete(user)
        await self.session.commit()
