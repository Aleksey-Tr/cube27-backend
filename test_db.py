import asyncio
from sqlalchemy import text
from backend.config.database_connection import engine

async def test_connection():
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT version();"))
            version = result.scalar()
            print(f"Версия PostgreSQL: {version}")
    except Exception as e:
        print("Ошибка при подключении к базе данных:")
        print(e)
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(test_connection())