# backend/tests/test_crud.py
import pytest
from app import crud, schemas
from app.auth import get_password_hash


@pytest.mark.asyncio
async def test_create_user(db_session, make_user_data):
    """Создание пользователя через CRUD"""
    user_data = make_user_data()
    user_schema = schemas.UserCreate(**user_data)
    
    user = await crud.create_user(db_session, user_schema)
    
    assert user.id is not None
    assert user.email == user_data["email"]
    assert user.hashed_password != user_data["password"]  # захеширован


@pytest.mark.asyncio
async def test_get_user_by_email(db_session, make_user_data):
    """Получение пользователя по email"""
    from app import models
    user_data = make_user_data()
    
    # Создаём напрямую
    user = models.User(
        username=user_data["username"],
        email=user_data["email"],
        hashed_password=get_password_hash(user_data["password"]),
    )
    db_session.add(user)
    await db_session.commit()
    
    # Ищем через CRUD
    found = await crud.get_user_by_email(db_session, user_data["email"])
    
    assert found is not None
    assert found.id == user.id


@pytest.mark.asyncio
async def test_authenticate_user_success(db_session, make_user_data):
    """Аутентификация с верными данными"""
    from app import models
    user_data = make_user_data()
    
    user = models.User(
        username=user_data["username"],
        email=user_data["email"],
        hashed_password=get_password_hash(user_data["password"]),
    )
    db_session.add(user)
    await db_session.commit()
    
    result = await crud.authenticate_user(db_session, user_data["email"], user_data["password"])
    
    assert result is not None
    assert result.email == user_data["email"]


@pytest.mark.asyncio
async def test_authenticate_user_wrong_password(db_session, make_user_data):
    """Аутентификация с неверным паролем"""
    from app import models
    user_data = make_user_data()
    
    user = models.User(
        username=user_data["username"],
        email=user_data["email"],
        hashed_password=get_password_hash("correct_pass"),
    )
    db_session.add(user)
    await db_session.commit()
    
    result = await crud.authenticate_user(db_session, user_data["email"], "wrong_pass")
    
    assert result is None

@pytest.mark.asyncio
async def test_create_task(db_session, make_user_data):
    """Создание задачи для пользователя"""
    from app import models, schemas
    from app.auth import get_password_hash
    
    # Создаём пользователя
    user_data = make_user_data()
    user = models.User(
        username=user_data["username"],
        email=user_data["email"],
        hashed_password=get_password_hash(user_data["password"]),
    )
    db_session.add(user)
    await db_session.commit()
    
    # Создаём задачу
    task_data = schemas.TaskCreate(
        title="Тестовая задача",
        description="Описание для теста",
        status="todo"
    )
    
    task = await crud.create_task(db_session, task_data, user_id=user.id)
    
    assert task.id is not None
    assert task.title == "Тестовая задача"
    assert task.user_id == user.id
    assert task.status == "todo"


@pytest.mark.asyncio
async def test_get_tasks_by_user(db_session, make_user_data):
    """Получение списка задач пользователя"""
    from app import models, schemas
    from app.auth import get_password_hash
    
    user_data = make_user_data()
    user = models.User(
        username=user_data["username"],
        email=user_data["email"],
        hashed_password=get_password_hash(user_data["password"]),
    )
    db_session.add(user)
    await db_session.commit()
    
    # Создаём 3 задачи
    for i in range(3):
        task_data = schemas.TaskCreate(title=f"Задача {i}", status="todo")
        await crud.create_task(db_session, task_data, user_id=user.id)
    
    # Получаем задачи (адаптируйте имя функции: get_tasks / get_user_tasks)
    try:
        tasks = await crud.get_tasks(db_session, user_id=user.id)
    except AttributeError:
        tasks = await crud.get_user_tasks(db_session, user_id=user.id)
    
    assert len(tasks) == 3
    assert all(t.user_id == user.id for t in tasks)


@pytest.mark.asyncio
async def test_update_task(db_session, make_user_data):
    """Обновление задачи — ИСПРАВЛЕНО: параметр 'update', не 'update_data'"""
    from app import models, schemas
    from app.auth import get_password_hash
    
    user_data = make_user_data()
    user = models.User(
        username=user_data["username"],
        email=user_data["email"],
        hashed_password=get_password_hash(user_data["password"]),
    )
    db_session.add(user)
    await db_session.commit()
    
    # Создаём задачу
    task_data = schemas.TaskCreate(title="Старый заголовок", status="todo")
    task = await crud.create_task(db_session, task_data, user_id=user.id)
    
    # Обновляем — ⚠️ параметр называется 'update', не 'update_data'!
    update = schemas.TaskUpdate(title="Новый заголовок", status="done")
    updated = await crud.update_task(db_session, task.id, user.id, update)
    
    assert updated.title == "Новый заголовок"
    assert updated.status == "done"


@pytest.mark.asyncio
async def test_delete_task(db_session, make_user_data):
    """Удаление задачи"""
    from app import models, schemas
    from app.auth import get_password_hash
    
    user_data = make_user_data()
    user = models.User(
        username=user_data["username"],
        email=user_data["email"],
        hashed_password=get_password_hash(user_data["password"]),
    )
    db_session.add(user)
    await db_session.commit()
    
    # Создаём задачу
    task_data = schemas.TaskCreate(title="Удалить меня", status="todo")
    task = await crud.create_task(db_session, task_data, user_id=user.id)
    
    # Удаляем
    result = await crud.delete_task(db_session, task.id, user.id)
    assert result is True
    
    # Проверяем удаление
    deleted = await crud.get_task(db_session, task.id, user.id)
    assert deleted is None


# === Тесты безопасности: доступ к чужим данным ===

@pytest.mark.asyncio
async def test_cannot_get_other_user_task(db_session, make_user_data):
    """Нельзя получить задачу другого пользователя"""
    from app import models, schemas
    from app.auth import get_password_hash
    
    # Два пользователя
    user1_data = make_user_data()
    user2_data = make_user_data()
    
    user1 = models.User(username=user1_data["username"], email=user1_data["email"], hashed_password=get_password_hash(user1_data["password"]))
    user2 = models.User(username=user2_data["username"], email=user2_data["email"], hashed_password=get_password_hash(user2_data["password"]))
    db_session.add_all([user1, user2])
    await db_session.commit()
    
    # Создаём задачу для user1
    task_data = schemas.TaskCreate(title="Секретная задача", status="todo")
    task = await crud.create_task(db_session, task_data, user_id=user1.id)
    
    # Пытаемся получить задачу через user2 (не должен найти)
    result = await crud.get_task(db_session, task.id, user_id=user2.id)
    
    assert result is None  # доступ запрещён


@pytest.mark.asyncio
async def test_cannot_update_other_user_task(db_session, make_user_data):
    """Нельзя обновить задачу другого пользователя — ИСПРАВЛЕНО"""
    from app import models, schemas
    from app.auth import get_password_hash
    
    user1_data = make_user_data()
    user2_data = make_user_data()
    
    user1 = models.User(username=user1_data["username"], email=user1_data["email"], hashed_password=get_password_hash(user1_data["password"]))
    user2 = models.User(username=user2_data["username"], email=user2_data["email"], hashed_password=get_password_hash(user2_data["password"]))
    db_session.add_all([user1, user2])
    await db_session.commit()
    
    # Создаём задачу для user1
    task_data = schemas.TaskCreate(title="Чужая задача", status="todo")
    task = await crud.create_task(db_session, task_data, user_id=user1.id)
    
    # Пытаемся обновить от имени user2
    update = schemas.TaskUpdate(title="Взломано!")
    
    # ⚠️ Параметр 'update', не 'update_data'!
    result = await crud.update_task(db_session, task.id, user2.id, update)
    
    # Должно вернуть None или не менять данные
    if result is not None:
        # Проверяем, что задача НЕ изменилась (или вернулась старая)
        assert result.title != "Взломано!" or result.id != task.id


# === Тесты для пользователя: удаление (если есть) ===

@pytest.mark.asyncio
async def test_delete_user(db_session, make_user_data):
    """Удаление пользователя — только если функция есть"""
    from app import models
    from app.auth import get_password_hash
    
    user_data = make_user_data()
    user = models.User(
        username=user_data["username"],
        email=user_data["email"],
        hashed_password=get_password_hash(user_data["password"]),
    )
    db_session.add(user)
    await db_session.commit()
    
    # Проверяем, есть ли функция delete_user
    if hasattr(crud, 'delete_user'):
        result = await crud.delete_user(db_session, user.id)
        assert result is True
        
        deleted = await crud.get_user_by_email(db_session, user.email)
        assert deleted is None
    else:
        pytest.skip("Функция delete_user не реализована")
