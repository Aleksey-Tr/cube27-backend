from fastapi import HTTPException, status

from database import get_session
from orm.meter_reading_orm import MeterReadingORM
from orm.user_orm import UserORM
from repositories.meter_readings_repo import MeterReadingsRepository
from repositories.meters_repo import MetersRepository
from roles import UserRole
from schemas.meter_reading_schemas import MeterReadingCreate, MeterReadingStatusUpdate
from schemas.meter_schemas import MeterType


class MeterReadingsService:
    @staticmethod
    async def get_all_readings(current_user: UserORM) -> list[MeterReadingORM]:
        user_role = current_user.role.lower().strip() if current_user.role else ""
        if user_role in (UserRole.OWNER.value, UserRole.ADMIN.value):
            meter_type = None
        elif user_role == UserRole.CHIEF_POWER_ENGINEER.value:
            meter_type = MeterType.ELECTRICITY.value
        elif user_role == UserRole.CHIEF_EMO.value:
            meter_type = MeterType.WATER.value
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Недостаточно прав для просмотра показаний",
            )

        async with get_session() as session:
            return await MeterReadingsRepository(session).get_all(meter_type=meter_type)

    @staticmethod
    async def update_status(
        reading_id: int, data: MeterReadingStatusUpdate, current_user: UserORM,
    ) -> MeterReadingORM:
        user_role = current_user.role.lower().strip() if current_user.role else ""
        staff_types = {
            UserRole.CHIEF_POWER_ENGINEER.value: MeterType.ELECTRICITY.value,
            UserRole.CHIEF_EMO.value: MeterType.WATER.value,
        }
        if user_role not in (UserRole.OWNER.value, UserRole.ADMIN.value, *staff_types):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Недостаточно прав для изменения статуса показания",
            )

        async with get_session() as session:
            repo = MeterReadingsRepository(session)
            reading = await repo.get_by_id(reading_id)
            if reading is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Показание с ID {reading_id} не найдено",
                )

            if user_role in staff_types:
                allowed_type = staff_types[user_role]
                if reading.meter is None or reading.meter.meter_type.lower().strip() != allowed_type:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Для вашей роли разрешены только счётчики типа '{allowed_type}'",
                    )

            reading = await repo.update_status(reading, data.status)
            await session.commit()
            return reading

    @staticmethod
    async def create_reading(
        meter_id: int, data: MeterReadingCreate, current_user: UserORM,
    ) -> MeterReadingORM:
        user_role = current_user.role.lower().strip() if current_user.role else ""
        staff_types = {
            UserRole.CHIEF_POWER_ENGINEER.value: MeterType.ELECTRICITY.value,
            UserRole.CHIEF_EMO.value: MeterType.WATER.value,
        }
        admin_roles = (UserRole.OWNER.value, UserRole.ADMIN.value)
        if user_role not in (*admin_roles, UserRole.COMPANY.value, *staff_types):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Недостаточно прав для передачи показаний",
            )

        async with get_session() as session:
            meter = await MetersRepository(session).get_by_id(meter_id)
            if meter is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Счётчик с ID {meter_id} не найден",
                )

            repo = MeterReadingsRepository(session)
            if user_role == UserRole.COMPANY.value:
                if not current_user.company_id or not await repo.is_current_tenant(premise_id=meter.premise_id, company_id=current_user.company_id):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="У вашей компании нет действующего договора аренды этого помещения",
                    )
            elif user_role in staff_types:
                allowed_type = staff_types[user_role]
                if meter.meter_type.lower().strip() != allowed_type:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Для вашей роли разрешены только счётчики типа '{allowed_type}'",
                    )

            reading = await repo.create(meter_id=meter.id, user_id=current_user.id, value=data.value)
            await session.commit()
            return reading
