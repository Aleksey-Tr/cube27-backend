from decimal import Decimal
from fastapi import HTTPException, status

from database import get_session
from orm.contract_orm import ContractORM
from orm.premise_orm import PremiseORM
from orm.user_orm import UserORM
from repositories.premises_repo import PremisesRepository
from schemas.premise_schemas import (
    PremiseAssignRequest,
    PremiseCreate,
    PremiseUpdate,
    TenantPremiseResponse,
)


class PremisesService:
    """Сервис управления помещениями и арендой."""

    @classmethod
    async def get_all(
        cls,
        status_filter: str | None = None,
        floor: int | None = None,
        min_area: Decimal | None = None,
        max_area: Decimal | None = None,
        min_price: Decimal | None = None,
        max_price: Decimal | None = None,
        search: str | None = None,
    ) -> list[PremiseORM]:
        async with get_session() as session:
            repo = PremisesRepository(session)
            return await repo.get_all(
                status=status_filter,
                floor=floor,
                min_area=min_area,
                max_area=max_area,
                min_price=min_price,
                max_price=max_price,
                search=search,
            )

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
    async def get_my_premises(
        cls, current_user: UserORM
    ) -> list[TenantPremiseResponse]:
        """Возвращает список помещений компании текущего авторизованного арендатора."""
        if not current_user.company_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="К вашей учетной записи не привязана компания",
            )

        async with get_session() as session:
            repo = PremisesRepository(session)
            return await repo.get_by_company_id(current_user.company_id)

    @classmethod
    async def get_premises_by_company_id(
        cls, company_id: int
    ) -> list[TenantPremiseResponse]:
        """Возвращает список помещений конкретной компании (для администратора)."""
        async with get_session() as session:
            repo = PremisesRepository(session)
            return await repo.get_by_company_id(company_id)

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
    async def assign(
        cls, premise_id: int, data: PremiseAssignRequest
    ) -> ContractORM:
        async with get_session() as session:
            repo = PremisesRepository(session)
            premise = await repo.get_by_id(premise_id)
            if not premise:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Помещение с ID {premise_id} не найдено",
                )
            try:
                return await repo.assign_to_company(
                    premise=premise,
                    company_id=data.company_id,
                    contract_number=data.contract_number,
                    start_date=data.start_date,
                    end_date=data.end_date,
                )
            except ValueError as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=str(e),
                )

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
