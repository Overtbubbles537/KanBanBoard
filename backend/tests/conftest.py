# backend/tests/conftest.py
import pytest
import pytest_asyncio
import tempfile
import os
from pathlib import Path
from sqlalchemy import text

from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.database import Base, get_db
from app.auth import get_password_hash
from main import app
from app import models


# Тестовая БД 
@pytest.fixture(scope="session")
def test_db_path():
    """Создаёт путь к тестовой БД"""
    Path("tests_temp").mkdir(exist_ok=True)
    return "sqlite+aiosqlite:///tests_temp/test.db"


@pytest_asyncio.fixture(scope="session")
async def engine(test_db_path):
    """Движок БД: один на все тесты"""
    db_file = test_db_path.replace("sqlite+aiosqlite:///", "")
    if os.path.exists(db_file):
        os.remove(db_file)
    
    engine = create_async_engine(test_db_path, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()
    
    # Чистим за собой
    if os.path.exists(db_file):
        os.remove(db_file)


@pytest_asyncio.fixture(scope="function")
async def db_session(engine):
    """Сессия БД для одного теста"""
    async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    
    async with async_session() as session:
        yield session
        try:
            await session.execute(text("DELETE FROM comments"))
        except:
            pass  # таблица может не существовать
        try:
            await session.execute(text("DELETE FROM tasks"))
        except:
            pass
        try:
            await session.execute(text("DELETE FROM users"))
        except:
            pass
        await session.commit()


@pytest_asyncio.fixture(scope="function")
async def client(db_session):
    """HTTP-клиент для тестов эндпоинтов"""
    app.dependency_overrides[get_db] = lambda: db_session
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.fixture
def make_user_data():
    """Фабрика данных пользователя — каждый вызов даёт уникальные данные"""
    import uuid
    def _make(**overrides):
        uid = str(uuid.uuid4())[:8]
        data = {
            "username": f"user_{uid}",
            "email": f"{uid}@test.com",
            "password": "TestPass123!"
        }
        data.update(overrides)
        return data
    return _make