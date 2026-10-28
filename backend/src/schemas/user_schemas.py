from pydantic import BaseModel, ConfigDict, EmailStr, Field


class CompanyBriefResponse(BaseModel):
    id: int
    name: str
    inn: str
    address: str | None = None

    model_config = ConfigDict(from_attributes=True)


class UserRegisterRequest(BaseModel):
    """Схема самостоятельной регистрации компании-арендатора (подача заявки)."""

    email: EmailStr = Field(description="Email арендатора для входа")
    password: str = Field(min_length=6, description="Пароль пользователя (минимум 6 символов)")
    first_name: str = Field(min_length=1, max_length=100, description="Имя контактного лица")
    last_name: str = Field(min_length=1, max_length=100, description="Фамилия контактного лица")
    phone: str | None = Field(default=None, max_length=20, description="Номер телефона")
    company_name: str = Field(min_length=1, max_length=255, description="Название компании арендатора")
    company_inn: str = Field(min_length=10, max_length=12, description="ИНН компании (10 или 12 цифр)")
    company_address: str | None = Field(default=None, description="Юридический адрес компании")


class UserCreateRequest(BaseModel):
    """Схема создания пользователя арендодателем (owner или admin).

    Если создается компания-арендатор (role_name='company'), то создается запись компании
    по переданным company_name и company_inn (или привязывается существующая).
    """

    email: EmailStr
    password: str = Field(min_length=6, description="Пароль пользователя (минимум 6 символов)")
    first_name: str = Field(min_length=1, max_length=100, description="Имя")
    last_name: str = Field(min_length=1, max_length=100, description="Фамилия")
    role_name: str = Field(
        description="Роль: owner, admin, lease_manager, chief_power_engineer, chief_emo, chief_engineer, chief_accountant, company"
    )
    phone: str | None = Field(default=None, max_length=20, description="Телефон")
    company_id: int | None = Field(
        default=None,
        description="ID существующей компании",
    )
    company_name: str | None = Field(
        default=None,
        description="Название компании (обязательно для новой компании-арендатора)",
    )
    company_inn: str | None = Field(
        default=None,
        description="ИНН компании (обязательно для новой компании-арендатора)",
    )
    company_address: str | None = Field(
        default=None,
        description="Адрес компании",
    )


class UserUpdateRequest(BaseModel):
    """Схема редактирования данных пользователя/представителя."""

    first_name: str | None = Field(default=None, max_length=100, description="Имя")
    last_name: str | None = Field(default=None, max_length=100, description="Фамилия")
    phone: str | None = Field(default=None, max_length=20, description="Телефон")
    company_name: str | None = Field(default=None, max_length=255, description="Название компании")
    company_address: str | None = Field(default=None, description="Адрес компании")


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserStatusUpdateRequest(BaseModel):
    """Схема изменения статуса активности пользователя (подтверждение/блокировка)."""

    is_active: bool = Field(description="Флаг активности: true — подтвержден/активен, false — заблокирован/ожидает")


class UserResponse(BaseModel):
    id: int
    email: str
    first_name: str
    last_name: str
    phone: str | None = None
    role_id: int
    role_name: str | None = None
    company_id: int | None = None
    company: CompanyBriefResponse | None = None
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class UserMeResponse(UserResponse):
    """Схема профиля текущего пользователя."""
    pass


class UserRegisterResponse(BaseModel):
    """Ответ после самостоятельной регистрации заявки компании-арендатора."""
    message: str
    user: UserResponse
