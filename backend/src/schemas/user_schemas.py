from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreateRequest(BaseModel):
    """Схема создания пользователя согласно иерархии прав."""

    email: EmailStr
    password: str = Field(min_length=6, description="Пароль пользователя (минимум 6 символов)")
    first_name: str = Field(min_length=1, max_length=100, description="Имя")
    last_name: str = Field(min_length=1, max_length=100, description="Фамилия")
    role_name: str = Field(
        description="Роль пользователя: owner, admin, company-owner, company-electrician, company-plumber"
    )
    company_id: int | None = Field(
        default=None,
        description="ID компании",
    )
    phone: str | None = Field(default=None, max_length=20, description="Телефон")


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    email: str
    first_name: str
    last_name: str
    role_id: int
    company_id: int | None
    phone: str | None
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class UserMeResponse(BaseModel):
    """Схема профиля текущего пользователя."""

    id: int
    email: str
    first_name: str
    last_name: str
    role_id: int
    role_name: str | None = None
    company_id: int | None = None
    phone: str | None = None
    is_active: bool

    model_config = ConfigDict(from_attributes=True)
