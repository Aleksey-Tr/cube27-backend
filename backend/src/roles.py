from enum import Enum


class UserRole(str, Enum):
    """Роли пользователей системы Cube27 по ТЗ."""

    OWNER = "owner"                                     # Владелец системы (самый главный)
    ADMIN = "admin"                                     # Администратор (подчинённый после owner)
    LEASE_MANAGER = "lease_manager"                     # Менеджер по аренде
    CHIEF_POWER_ENGINEER = "chief_power_engineer"       # Главный энергетик
    CHIEF_EMO = "chief_emo"                             # Начальник службы ЭМО
    CHIEF_ENGINEER = "chief_engineer"                   # Главный инженер
    CHIEF_ACCOUNTANT = "chief_accountant"               # Главный бухгалтер
    COMPANY = "company"                                 # Компания-арендатор (единая роль арендатора)


# Матрица прав: роль создателя -> роли, которыми он может управлять
ROLE_PERMISSIONS: dict[str, set[str]] = {
    # 1. owner: управление абсолютно всеми ролями
    UserRole.OWNER.value: {
        UserRole.OWNER.value,
        UserRole.ADMIN.value,
        UserRole.LEASE_MANAGER.value,
        UserRole.CHIEF_POWER_ENGINEER.value,
        UserRole.CHIEF_EMO.value,
        UserRole.CHIEF_ENGINEER.value,
        UserRole.CHIEF_ACCOUNTANT.value,
        UserRole.COMPANY.value,
    },
    # 2. admin: управляет сотрудниками компании и арендаторами (не может управлять owner и admin)
    UserRole.ADMIN.value: {
        UserRole.LEASE_MANAGER.value,
        UserRole.CHIEF_POWER_ENGINEER.value,
        UserRole.CHIEF_EMO.value,
        UserRole.CHIEF_ENGINEER.value,
        UserRole.CHIEF_ACCOUNTANT.value,
        UserRole.COMPANY.value,
    },
    # 3. Сотрудники и компании-арендаторы прав на создание других пользователей не имеют
    UserRole.LEASE_MANAGER.value: set(),
    UserRole.CHIEF_POWER_ENGINEER.value: set(),
    UserRole.CHIEF_EMO.value: set(),
    UserRole.CHIEF_ENGINEER.value: set(),
    UserRole.CHIEF_ACCOUNTANT.value: set(),
    UserRole.COMPANY.value: set(),
}
