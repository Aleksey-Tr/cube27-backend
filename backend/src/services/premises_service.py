from fastapi import HTTPException, status

from database import get_session
from orm.premise_orm import PremiseORM
from repositories.premises_repo import PremisesRepository
from schemas.premise_schemas import PremiseCreate, PremiseUpdate


class PremisesService:
    """Сервис управления помещениями.
    """

    @classmethod
    async def get_all(
        cls,
        status_filter: str | None = None,
        floor: int | None = None,
    ) -> list[PremiseORM]:
        async with get_session() as session:
            repo = PremisesRepository(session)
            return await repo.get_all(status=status_filter, floor=floor)

    @classmethod
    async def get_by_id(cls, premise_id: int) -> PremiseORM:
        async with get_session() as session:
            repo = PremisesRepository(session)
            premise = await repo.get_by_id(premise_id)
            if not premise:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Помещение с ID {premise_id} не найдено",
                )
            return premise

    @classmethod
    async def create(cls, data: PremiseCreate) -> PremiseORM:
        async with get_session() as session:
            repo = PremisesRepository(session)
            return await repo.create(data)

    @classmethod
    async def update(
        cls, premise_id: int, data: PremiseUpdate
    ) -> PremiseORM:
        async with get_session() as session:
            repo = PremisesRepository(session)
            premise = await repo.get_by_id(premise_id)
            if not premise:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Помещение с ID {premise_id} не найдено",
                )
            return await repo.update(premise, data)

    @classmethod
    async def delete(cls, premise_id: int) -> None:
        async with get_session() as session:
            repo = PremisesRepository(session)
            premise = await repo.get_by_id(premise_id)
            if not premise:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Помещение с ID {premise_id} не найдено",
                )
            await repo.delete(premise)
