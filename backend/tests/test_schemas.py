# backend/tests/test_schemas.py
import pytest
from pydantic import ValidationError
from app.schemas import UserCreate, TaskCreate


class TestUserCreate:
    """Простые тесты схемы пользователя"""
    
    def test_valid_user(self):
        user = UserCreate(
            username="testuser",
            email="test@example.com",
            password="SecurePass123!"
        )
        assert user.username == "testuser"
        assert user.email == "test@example.com"
    
    def test_short_password_fails(self):
        with pytest.raises(ValidationError):
            UserCreate(
                username="test",
                email="test@example.com",
                password="123"  # слишком короткий
            )
    
    def test_bad_email_fails(self):
        with pytest.raises(ValidationError):
            UserCreate(
                username="test",
                email="not-email",
                password="SecurePass123!"
            )


class TestTaskCreate:
    """Простые тесты схемы задачи"""
    
    def test_minimal_task(self):
        task = TaskCreate(title="Просто задача")
        assert task.title == "Просто задача"
    
    def test_task_with_status(self):
        # Используем строки — работает с любым enum
        task = TaskCreate(title="Test", status="todo")
        # Гибкая проверка: может быть строка или enum
        status_val = task.status.value if hasattr(task.status, 'value') else task.status
        assert status_val == "todo"
    
    def test_empty_title_fails(self):
        with pytest.raises(ValidationError):
            TaskCreate(title="")  # пустой заголовок невалиден