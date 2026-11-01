from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, ValidationError
import sys

class Settings(BaseSettings):
    DATABASE_URL: str = Field(min_length=1)
    JWT_SECRET_KEY: str = Field(min_length=6)
    JWT_ALGORITHM: str = Field(min_length=1)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(ge=60)
    COOKIE_KEY: str = "access_token"
    COOKIE_SECURE: bool = False

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        extra="ignore",
    )

try:
    settings = Settings()
except ValidationError as e:
    print("Ошибка конфигурации при запуске приложения!\n Проверьте файл .env или переменные окружения\n")

    for error in e.errors():
        field_name = " -> ".join(str(loc) for loc in error["loc"])

        if error["type"] == "missing":
            print(f"Переменная {field_name} обязательна, но не заведена.")
        else:
            print(f"Ошибка в поле {field_name}: {error['msg']}")
    sys.exit(1)