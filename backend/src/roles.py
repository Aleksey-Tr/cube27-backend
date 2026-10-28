from enum import Enum


class UserRole(str, Enum):
    """4 основных уровня ролей пользователей системы Cube27."""

    OWNER = "owner"                                     # Владелец системы (может управлять всем)
    ADMIN = "admin"                                     # Администратор (управляет company-owner и ниже)
    COMPANY_OWNER = "company-owner"                     # Владелец компании/арендатор (управляет работниками своей компании)
    COMPANY_ELECTRICIAN = "company-electrician"         # Электрик компании
    COMPANY_PLUMBER = "company-plumber"                 # Сантехник компании


# Единый список разрешений: роль инициатора -> роли, которыми он может управлять (создавать / удалять)
ROLE_PERMISSIONS: dict[str, set[str]] = {
    # 1. owner: управление абсолютно всеми ролями
    UserRole.OWNER.value: {
        UserRole.OWNER.value,
        UserRole.ADMIN.value,
        UserRole.COMPANY_OWNER.value,
        UserRole.COMPANY_ELECTRICIAN.value,
        UserRole.COMPANY_PLUMBER.value,
    },
    # 2. admin: управление company-owner и линейными работниками
    UserRole.ADMIN.value: {
        UserRole.COMPANY_OWNER.value,
        UserRole.COMPANY_ELECTRICIAN.value,
        UserRole.COMPANY_PLUMBER.value,
    },
    # 3. company-owner: управление только работниками своей компании
    UserRole.COMPANY_OWNER.value: {
        UserRole.COMPANY_ELECTRICIAN.value,
        UserRole.COMPANY_PLUMBER.value,
    },
    # 4. Линейные работники (электрик, сантехник): прав управления нет
    UserRole.COMPANY_ELECTRICIAN.value: set(),
    UserRole.COMPANY_PLUMBER.value: set(),
}
