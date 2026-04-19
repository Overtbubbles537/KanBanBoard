from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from enum import Enum


# ====== Статусы задач ======
class TaskStatus(str, Enum):
    TODO = "todo"
    IN_PROGRESS = "in-progress"
    DONE = "done"


# ====== Схемы для пользователя ======
class UserBase(BaseModel):
    """Базовые поля пользователя"""

    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr


class UserCreate(UserBase):
    """Данные для регистрации"""

    password: str = Field(..., min_length=6)


class UserLogin(BaseModel):
    """Данные для входа"""

    email: EmailStr
    password: str


class UserResponse(UserBase):
    """Данные которые отдаём клиенту (без пароля)"""

    id: int
    is_active: bool
    otp_enabled: bool = False
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserInDB(UserResponse):
    """Внутреннее представление (с паролем)"""

    hashed_password: str
    otp_secret: Optional[str] = None


# ====== Схемы для задач ======
class TaskBase(BaseModel):
    """Базовые поля задачи"""

    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    status: TaskStatus = TaskStatus.TODO
    order: int = 0


class TaskCreate(TaskBase):
    """Данные для создания задачи"""

    pass


class TaskUpdate(BaseModel):
    """Данные для обновления (все поля необязательные)"""

    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    order: Optional[int] = None


class TaskResponse(TaskBase):
    """Данные которые отдаём клиенту"""

    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ====== Схемы для токенов ======
class Token(BaseModel):
    """Ответ при успешном входе"""

    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class TokenData(BaseModel):
    """Данные внутри JWT токена"""

    user_id: Optional[int] = None
    email: Optional[str] = None
