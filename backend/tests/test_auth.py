# backend/tests/test_auth.py
import pytest
from app.auth import verify_password, get_password_hash, create_access_token, decode_access_token


# === Тесты функций (быстрые, без БД) ===

def test_password_hash_and_verify():
    """Пароль хешируется и проверяется"""
    password = "MyPass123!"
    hashed = get_password_hash(password)
    
    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("wrong", hashed) is False


def test_access_token_works():
    """Токен создаётся и декодируется"""
    data = {"sub": "test@test.com", "user_id": 42}
    token = create_access_token(data)
    
    assert isinstance(token, str)
    payload = decode_access_token(token)
    assert payload is not None
    assert payload["user_id"] == 42


# === Тесты эндпоинтов (интеграционные) ===

@pytest.mark.asyncio
async def test_register_new_user(client, make_user_data):
    """Регистрация нового пользователя"""
    user_data = make_user_data()
    
    response = await client.post("/auth/register", json=user_data)
    
    # Ваш эндпоинт может возвращать 200 или 201 — проверьте и поставьте нужное
    assert response.status_code in [200, 201]
    
    result = response.json()
    assert result["email"] == user_data["email"]
    assert "password" not in result  # пароль не возвращается
    assert "hashed_password" not in result


@pytest.mark.asyncio
async def test_login_with_correct_password(client, db_session, make_user_data):
    """Вход с верным паролем"""
    # Создаём пользователя напрямую в БД
    from app import models
    user_data = make_user_data()
    
    user = models.User(
        username=user_data["username"],
        email=user_data["email"],
        hashed_password=get_password_hash(user_data["password"]),
    )
    db_session.add(user)
    await db_session.commit()
    
    # Пробуем войти
    response = await client.post("/auth/login", json={
        "email": user_data["email"],
        "password": user_data["password"]
    })
    
    assert response.status_code == 200
    result = response.json()
    assert "access_token" in result
    assert result["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_with_wrong_password(client, db_session, make_user_data):
    """Вход с неверным паролем"""
    from app import models
    user_data = make_user_data()
    
    user = models.User(
        username=user_data["username"],
        email=user_data["email"],
        hashed_password=get_password_hash("correct_password"),
    )
    db_session.add(user)
    await db_session.commit()
    
    response = await client.post("/auth/login", json={
        "email": user_data["email"],
        "password": "wrong_password"
    })
    
    assert response.status_code == 401  # или 400 — проверьте ваш код

    