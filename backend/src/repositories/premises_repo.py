from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from orm.premise_orm import PremiseORM
from schemas.premise_schemas import PremiseCreate, PremiseUpdate


class PremisesRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all(
        self,
        status: str | None = None,
        floor: int | None = None,
    ) -> list[PremiseORM]:
        stmt = select(PremiseORM)
        if status:
            stmt = stmt.where(PremiseORM.status == status)
        if floor is not None:
            stmt = stmt.where(PremiseORM.floor == floor)
        stmt = stmt.order_by(PremiseORM.id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(self, premise_id: int) -> PremiseORM | None:
        return await self.session.get(PremiseORM, premise_id)

    async def create(self, data: PremiseCreate) -> PremiseORM:
        premise = PremiseORM(
            floor=data.floor,
            room_number=data.room_number,
            area=data.area,
            price=data.price,
            status=data.status,
        )
        self.session.add(premise)
        await self.session.commit()
        await self.session.refresh(premise)
        return premise

    async def update(
        self, premise: PremiseORM, data: PremiseUpdate
    ) -> PremiseORM:
        update_dict = data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            setattr(premise, key, value)
        await self.session.commit()
        await self.session.refresh(premise)
        return premise

    async def delete(self, premise: PremiseORM) -> None:
        await self.session.delete(premise)
        await self.session.commit()
