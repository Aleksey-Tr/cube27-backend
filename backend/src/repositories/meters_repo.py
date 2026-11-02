from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from orm.contract_orm import ContractORM
from orm.contract_premise_orm import ContractPremiseORM
from orm.meter_orm import MeterORM


class MetersRepository:
    """Репозиторий для работы с приборами учета (счетчиками)."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, meter_id: int) -> MeterORM | None:
        """Поиск счетчика по ID."""
        return await self.session.get(MeterORM, meter_id)

    async def get_by_serial_number(self, serial_number: str) -> MeterORM | None:
        """Поиск счетчика по уникальному серийному номеру."""
        stmt = select(MeterORM).where(MeterORM.serial_number == serial_number.strip())
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_all(
        self,
        premise_id: int | None = None,
        meter_type: str | None = None
    ) -> list[MeterORM]:
        """Получение списка счетчиков с фильтрацией по помещению, типу и категории прав."""
        stmt = select(MeterORM)

        if premise_id is not None:
            stmt = stmt.where(MeterORM.premise_id == premise_id)

        if meter_type:
            stmt = stmt.where(MeterORM.meter_type.ilike(f"%{meter_type.strip()}%"))

        stmt = stmt.order_by(MeterORM.id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def is_premise_rented_by_company(
        self, premise_id: int, company_id: int
    ) -> bool:
        """Проверяет, арендует ли указанная компания данное помещение по активному договору."""
        stmt = (
            select(ContractPremiseORM)
            .join(ContractORM, ContractORM.id == ContractPremiseORM.contract_id)
            .where(
                ContractPremiseORM.premise_id == premise_id,
                ContractORM.company_id == company_id,
                ContractORM.status.in_(["Active"]),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalars().first() is not None

    async def create(
        self,
        premise_id: int,
        meter_type: str,
        serial_number: str,
    ) -> MeterORM:
        """Создает и сохраняет новую запись счетчика в базе данных."""
        meter = MeterORM(
            premise_id=premise_id,
            meter_type=meter_type.strip(),
            serial_number=serial_number.strip(),
        )
        self.session.add(meter)
        await self.session.flush()
        return meter
