from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./kanban.db")

# Асинхронный движок
engine = create_async_engine(
    DATABASE_URL,
    echo=True,  # Показывает SQL запросы в консоли
    connect_args={"check_same_thread": False},
)

# Асинхронная фабрика сессий
AsyncSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

# Базовый класс для моделей
Base = declarative_base()


# Генератор асинхронной сессии
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
