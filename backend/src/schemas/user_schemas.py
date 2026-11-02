from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator


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
    phone: str = Field(max_length=20, description="Номер телефона")
    company_name: str = Field(min_length=1, max_length=255, description="Название компании арендатора")
    company_inn: str = Field(min_length=10, max_length=12, description="ИНН компании (10 или 12 цифр)")
    company_address: str | None = Field(default=None, description="Юридический адрес компании")


class UserCreateRequest(UserRegisterRequest):
    """Схема создания пользователя арендодателем (owner или admin).

    Если создается компания-арендатор (role='company'), то создается запись компании
    по переданным company_name и company_inn (или привязывается существующая).
    """

    role: str = Field(description="Роль: owner, admin, lease_manager, chief_power_engineer, chief_emo, chief_engineer, chief_accountant, company")
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

    @model_validator(mode="after")
    def validate_company_fields(self) -> "UserCreateRequest":
        is_company = self.role and self.role.lower().strip() == "company"
        has_id = self.company_id is not None
        has_name = bool(self.company_name and self.company_name.strip())
        has_inn = bool(self.company_inn and self.company_inn.strip())
        has_address = bool(self.company_address and self.company_address.strip())

        if is_company:
            # Нельзя указывать одновременно id и данные новой компании
            if has_id and (has_name or has_inn or has_address):
                raise ValueError("Укажите либо company_id, либо данные компании (company_name и company_inn), но не то и другое одновременно")
            # Должно быть указано либо id, либо данные компании (company_name и company_inn)
            if not has_id:
                if not has_name or not has_inn or not has_address:
                    raise ValueError("Для роли 'company' необходимо указать данные компании (company_name и company_inn)")
        else:
            if has_name or has_inn or has_address:
                raise ValueError("Данные компании (company_name, company_inn) указываются только при создании роли 'company'")
        return self


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
    phone: str
    role: str
    company_id: int | None
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
