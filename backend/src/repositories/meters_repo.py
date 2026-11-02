from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

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

    async def get_by_premise_id(self, premise_id: int) -> list[MeterORM]:
        """Получение списка счетчиков конкретного помещения."""
        stmt = (
            select(MeterORM)
            .where(MeterORM.premise_id == premise_id)
            .order_by(MeterORM.id)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

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
        await self.session.commit()
        await self.session.refresh(meter)
        return meter
