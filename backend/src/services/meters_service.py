from fastapi import HTTPException, status

from database import get_session
from orm.meter_orm import MeterORM
from orm.premise_orm import PremiseORM
from orm.user_orm import UserORM
from repositories.meters_repo import MetersRepository
from roles import UserRole
from schemas.meter_schemas import (
    MeterCreate,
    MeterType,
    MeterUpdate,
)


class MetersService:
    """Сервис управления приборами учета (счетчиками)."""

    @staticmethod
    def _check_management_access(current_user: UserORM, meter_type: str | None = None) -> None:
        user_role = current_user.role.lower().strip() if current_user.role else ""
        if user_role in (UserRole.OWNER.value, UserRole.ADMIN.value):
            return
        allowed_type = {
            UserRole.CHIEF_POWER_ENGINEER.value: MeterType.ELECTRICITY.value,
            UserRole.CHIEF_EMO.value: MeterType.WATER.value,
        }.get(user_role)
        if allowed_type is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Недостаточно прав для изменения или удаления счетчиков",
            )
        if meter_type is not None and meter_type.lower().strip() != allowed_type:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Для вашей роли разрешены только счетчики типа '{allowed_type}'",
            )

    @classmethod
    async def update_meter(
        cls, meter_id: int, data: MeterUpdate, current_user: UserORM
    ) -> MeterORM:
        cls._check_management_access(current_user)
        async with get_session() as session:
            repo = MetersRepository(session)
            meter = await repo.get_by_id(meter_id)
            if meter is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Счетчик с ID {meter_id} не найден",
                )
            cls._check_management_access(current_user, meter.meter_type)
            values = data.model_dump(exclude_unset=True, mode="json")
            if "meter_type" in values:
                cls._check_management_access(current_user, values["meter_type"])
            if "serial_number" in values:
                existing = await repo.get_by_serial_number(values["serial_number"])
                if existing is not None and existing.id != meter.id:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Счетчик с серийным номером '{values['serial_number']}' уже зарегистрирован (ID: {existing.id})",
                    )
            meter = await repo.update(meter, values)
            await session.commit()
            return meter

    @classmethod
    async def delete_meter(cls, meter_id: int, current_user: UserORM) -> None:
        async with get_session() as session:
            repo = MetersRepository(session)
            meter = await repo.get_by_id(meter_id)
            if meter is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Счетчик с ID {meter_id} не найден",
                )
            cls._check_management_access(current_user, meter.meter_type)
            await repo.delete(meter)
            await session.commit()

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
            meter = await repo.create(premise_id=premise_id,
                              meter_type=meter_type,
                              serial_number=clean_serial)
            await session.commit()
            return meter

    @classmethod
    async def get_premise_meters(
        cls,
        premise_id: int,
        current_user: UserORM,
    ) -> list[MeterORM]:
        """Возвращает счетчики конкретного помещения.

        Доступ:
        - owner / admin: доступ ко всем помещениям.
        - company (арендатор): только при наличии активного договора аренды на это помещение.
        """
        user_role = current_user.role.lower().strip() if current_user.role else ""

        # Проверка доступа
        if user_role not in (UserRole.COMPANY.value, UserRole.ADMIN.value, UserRole.OWNER.value, 
                             UserRole.CHIEF_EMO.value, UserRole.CHIEF_POWER_ENGINEER.value):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Доступ разрешен только администраторам или арендаторам данного помещения",
            )

        async with get_session() as session:
            premise = await session.get(PremiseORM, premise_id)
            if not premise:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Помещение с ID {premise_id} не найдено",
                )

            repo = MetersRepository(session)


            # Проверка аренды для арендатора
            meters_type = None
            if user_role == UserRole.COMPANY.value:
                if not current_user.company_id:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="К вашей учетной записи не привязана компания-арендатор",
                    )

                is_rented = await repo.is_premise_rented_by_company(
                    premise_id=premise_id,
                    company_id=current_user.company_id,
                )
                if not is_rented:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="У вашей компании нет активного договора аренды для данного помещения",
                    )
            elif user_role == UserRole.CHIEF_POWER_ENGINEER.value:
                meters_type = MeterType.ELECTRICITY.value
            elif user_role == UserRole.CHIEF_EMO.value:
                meters_type = MeterType.WATER.value

            return await repo.get_all(premise_id=premise_id, meter_type=meters_type)

    @classmethod
    async def get_all_meters(
        cls,
        current_user: UserORM,
        premise_id: int | None = None,
        meter_type: str | None = None,
    ) -> list[MeterORM]:
        """Возвращает список всех счетчиков с разделением прав доступа.

        - owner / admin: доступ ко всем счетчикам.
        - chief_power_engineer: доступ только к счетчикам электричества.
        - chief_emo: доступ только к счетчикам водоснабжения.
        """
        user_role = current_user.role.lower().strip() if current_user.role else ""

        if user_role in (UserRole.OWNER.value, UserRole.ADMIN.value):
            pass
        elif user_role == UserRole.CHIEF_POWER_ENGINEER.value:
            meter_type = MeterType.ELECTRICITY.value
        elif user_role == UserRole.CHIEF_EMO.value:
            meter_type = MeterType.WATER.value
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Недостаточно прав для просмотра списка счетчиков",
            )

        async with get_session() as session:
            repo = MetersRepository(session)
            return await repo.get_all(premise_id=premise_id, meter_type=meter_type)
