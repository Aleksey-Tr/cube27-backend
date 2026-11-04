from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from orm.contract_orm import ContractORM
from orm.contract_premise_orm import ContractPremiseORM
from orm.meter_reading_orm import MeterReadingORM


class MeterReadingsRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, reading_id: int) -> MeterReadingORM | None:
        stmt = (
            select(MeterReadingORM)
            .options(joinedload(MeterReadingORM.meter))
            .where(MeterReadingORM.id == reading_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_status(self, reading: MeterReadingORM, new_status: str) -> MeterReadingORM:
        reading.status = new_status
        await self.session.flush()
        return reading

    async def is_current_tenant(self, premise_id: int, company_id: int) -> bool:
        stmt = (
            select(ContractPremiseORM.premise_id)
            .join(ContractORM, ContractORM.id == ContractPremiseORM.contract_id)
            .where(
                ContractPremiseORM.premise_id == premise_id,
                ContractORM.company_id == company_id,
                ContractORM.status == "Active",
                ContractORM.start_date <= func.current_date(),
                ContractORM.end_date >= func.current_date(),
            )
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def create(self, meter_id: int, user_id: int, value: Decimal) -> MeterReadingORM:
        reading = MeterReadingORM(meter_id=meter_id, user_id=user_id, value=value, status="Pending")
        self.session.add(reading)
        await self.session.flush()
        await self.session.refresh(reading)
        return reading
