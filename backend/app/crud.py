from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Optional, List
from datetime import datetime

from app import models, schemas
from app.auth import get_password_hash, verify_password


# ====== ПОЛЬЗОВАТЕЛИ ======
async def get_user_by_email(db: AsyncSession, email: str) -> Optional[models.User]:
    result = await db.execute(select(models.User).where(models.User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[models.User]:
    result = await db.execute(select(models.User).where(models.User.id == user_id))
    return result.scalar_one_or_none()


async def create_user(db: AsyncSession, user_data: schemas.UserCreate) -> models.User:
    hashed_password = get_password_hash(user_data.password)
    db_user = models.User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password,
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user


async def authenticate_user(
    db: AsyncSession, email: str, password: str
) -> Optional[models.User]:
    user = await get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


# ====== ЗАДАЧИ ======
async def get_tasks(
    db: AsyncSession, user_id: int, skip: int = 0, limit: int = 100
) -> List[models.Task]:
    result = await db.execute(
        select(models.Task)
        .where(models.Task.user_id == user_id)
        .order_by(models.Task.order, models.Task.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()


async def get_task(
    db: AsyncSession, task_id: int, user_id: int
) -> Optional[models.Task]:
    result = await db.execute(
        select(models.Task)
        .where(models.Task.id == task_id)
        .where(models.Task.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def create_task(
    db: AsyncSession, task_data: schemas.TaskCreate, user_id: int
) -> models.Task:
    result = await db.execute(
        select(models.Task)
        .where(models.Task.user_id == user_id)
        .where(models.Task.status == task_data.status.value)
    )
    existing_tasks = result.scalars().all()
    max_order = len(existing_tasks)

    db_task = models.Task(
        title=task_data.title,
        description=task_data.description,
        status=task_data.status.value,
        order=max_order,
        user_id=user_id,
        deadline=task_data.deadline,
    )
    db.add(db_task)
    await db.commit()
    await db.refresh(db_task)
    return db_task


async def update_task(
    db: AsyncSession, task_id: int, user_id: int, task_update: schemas.TaskUpdate
) -> Optional[models.Task]:
    task = await get_task(db, task_id, user_id)
    if not task:
        return None

    update_data = task_update.model_dump(exclude_unset=True)
    if "status" in update_data:
        update_data["status"] = update_data["status"].value

    for field, value in update_data.items():
        setattr(task, field, value)

    task.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(task)
    return task


async def delete_task(db: AsyncSession, task_id: int, user_id: int) -> bool:
    task = await get_task(db, task_id, user_id)
    if not task:
        return False
    await db.delete(task)
    await db.commit()
    return True
