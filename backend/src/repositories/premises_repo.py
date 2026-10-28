from datetime import date
from decimal import Decimal
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from orm.company_orm import CompanyORM
from orm.contract_orm import ContractORM
from orm.contract_premise_orm import ContractPremiseORM
from orm.premise_orm import PremiseORM
from schemas.premise_schemas import PremiseCreate, PremiseUpdate, TenantPremiseResponse


class PremisesRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all(
        self,
        status: str | None = None,
        floor: int | None = None,
        min_area: Decimal | None = None,
        max_area: Decimal | None = None,
        min_price: Decimal | None = None,
        max_price: Decimal | None = None,
        search: str | None = None,
    ) -> list[PremiseORM]:
        stmt = select(PremiseORM)

        if status:
            stmt = stmt.where(PremiseORM.status == status.strip())
        if floor is not None:
            stmt = stmt.where(PremiseORM.floor == floor)
        if min_area is not None:
            stmt = stmt.where(PremiseORM.area >= min_area)
        if max_area is not None:
            stmt = stmt.where(PremiseORM.area <= max_area)
        if min_price is not None:
            stmt = stmt.where(PremiseORM.price >= min_price)
        if max_price is not None:
            stmt = stmt.where(PremiseORM.price <= max_price)
        if search:
            stmt = stmt.where(PremiseORM.room_number.ilike(f"%{search.strip()}%"))

        stmt = stmt.order_by(PremiseORM.id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(self, premise_id: int) -> PremiseORM | None:
        stmt = (
            select(PremiseORM)
            .options(selectinload(PremiseORM.contracts))
            .where(PremiseORM.id == premise_id)
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_by_company_id(self, company_id: int) -> list[TenantPremiseResponse]:
        """Возвращает все помещения, арендуемые конкретной компанией через договоры."""
        stmt = (
            select(PremiseORM, ContractORM)
            .join(ContractPremiseORM, ContractPremiseORM.premise_id == PremiseORM.id)
            .join(ContractORM, ContractORM.id == ContractPremiseORM.contract_id)
            .where(ContractORM.company_id == company_id)
            .order_by(PremiseORM.id)
        )
        result = await self.session.execute(stmt)
        rows = result.all()

        premises_list: list[TenantPremiseResponse] = []
        for premise, contract in rows:
            premises_list.append(
                TenantPremiseResponse(
                    id=premise.id,
                    room_number=premise.room_number,
                    floor=premise.floor,
                    area=premise.area,
                    price=premise.price,
                    status=premise.status,
                    contract_id=contract.id,
                    contract_number=contract.contract_number,
                    contract_status=contract.status,
                    start_date=contract.start_date,
                    end_date=contract.end_date,
                )
            )
        return premises_list

    async def create(self, data: PremiseCreate) -> PremiseORM:
        premise = PremiseORM(
            floor=data.floor,
            room_number=data.room_number.strip(),
            area=data.area,
            price=data.price,
            status=data.status.strip(),
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
            if isinstance(value, str):
                value = value.strip()
            setattr(premise, key, value)
        await self.session.commit()
        await self.session.refresh(premise)
        return premise

    async def assign_to_company(
        self,
        premise: PremiseORM,
        company_id: int,
        contract_number: str,
        start_date: date,
        end_date: date,
    ) -> ContractORM:
        """Привязывает помещение к компании через создание/привязку договора аренды."""
        # 1. Проверяем наличие компании
        company = await self.session.get(CompanyORM, company_id)
        if not company:
            raise ValueError(f"Компания с ID {company_id} не найдена")

        # 2. Ищем существующий договор с таким номером или создаем новый
        stmt = select(ContractORM).where(ContractORM.contract_number == contract_number.strip())
        result = await self.session.execute(stmt)
        contract = result.scalars().first()

        if not contract:
            contract = ContractORM(
                company_id=company_id,
                contract_number=contract_number.strip(),
                start_date=start_date,
                end_date=end_date,
                status="Active",
            )
            self.session.add(contract)
            await self.session.flush()

        # 3. Связываем помещение с договором
        link_stmt = select(ContractPremiseORM).where(
            ContractPremiseORM.contract_id == contract.id,
            ContractPremiseORM.premise_id == premise.id,
        )
        existing_link = (await self.session.execute(link_stmt)).scalars().first()
        if not existing_link:
            new_link = ContractPremiseORM(contract_id=contract.id, premise_id=premise.id)
            self.session.add(new_link)

        # 4. Обновляем статус помещения на 'Occupied' (Занято)
        premise.status = "Occupied"

        await self.session.commit()
        await self.session.refresh(contract)
        await self.session.refresh(premise)
        return contract

    async def delete(self, premise: PremiseORM) -> None:
        await self.session.delete(premise)
        await self.session.commit()
