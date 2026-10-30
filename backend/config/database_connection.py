import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

BASE_DIR = Path(__file__).resolve().parent.parent
env_path = BASE_DIR / ".env"

load_dotenv(dotenv_path=env_path)

DATABASE_URL = os.getenv("DATABASE_URL")

print(f"Текущая папка скрипта: {Path(__file__).resolve()}")
print(f"Значение DATABASE_URL: {DATABASE_URL}")

if not DATABASE_URL: raise ValueError("Переменная окружения DATABASE_URL не найдена в .env файле!")

engine = create_async_engine(DATABASE_URL, echo=True,)

AsyncSessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False,)

class Base(DeclarativeBase): pass

async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()