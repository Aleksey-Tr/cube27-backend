from fastapi import HTTPException, status

from database import get_session
from orm.meter_orm import MeterORM
from orm.premise_orm import PremiseORM
from orm.user_orm import UserORM
from repositories.meters_repo import MetersRepository
from roles import UserRole
from schemas.meter_schemas import (
    MeterCreate,
    MeterType
)


class MetersService:
    """Сервис управления приборами учета (счетчиками)."""

    @classmethod
    async def create_meter(
        cls,
        premise_id: int,
        data: MeterCreate,
        current_user: UserORM,
    ) -> MeterORM:
        """Создает новый счетчик для указанного помещения с проверкой прав доступа.

        - owner / admin: могут создавать счетчики любого типа.
        - chief_power_engineer: может создавать только счетчики электричества.
        - chief_emo: может создавать только счетчики водоснабжения.
        """
        user_role = current_user.role.lower().strip() if current_user.role else ""
        meter_type = data.meter_type.lower().strip() if data.meter_type else ""

        # 2. Проверка ограничений по типам счетчиков для специалистов
        if user_role == UserRole.CHIEF_POWER_ENGINEER.value and not meter_type == MeterType.ELECTRICITY.value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Главный энергетик может создавать только счетчики электричества",
            )
        elif user_role == UserRole.CHIEF_EMO.value and not meter_type == MeterType.WATER.value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Начальник службы ЭМО может создавать только счетчики водоснабжения",
            )

        # 4. Проверка существования помещения и уникальности серийного номера
        async with get_session() as session:
            premise = await session.get(PremiseORM, premise_id)
            if not premise:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Помещение с ID {premise_id} не найдено",
                )

            repo = MetersRepository(session)
            clean_serial = data.serial_number.strip()
            existing = await repo.get_by_serial_number(clean_serial)
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Счетчик с серийным номером '{clean_serial}' уже зарегистрирован (ID: {existing.id})",
                )
            return await repo.create(
                premise_id=premise_id,
                meter_type=meter_type,
                serial_number=clean_serial,
            )
