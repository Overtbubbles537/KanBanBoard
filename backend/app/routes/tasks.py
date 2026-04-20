import asyncio
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app import schemas, models, crud
from app.database import get_db
from app.dependencies import get_current_user

router = APIRouter(prefix="/tasks", tags=["tasks"])

# Создаём пул потоков
thread_pool = ThreadPoolExecutor(max_workers=3)


# Синхронная функция, которая выполнится в отдельном потоке
def heavy_background_task(task_id: int):
    current = threading.current_thread()
    print(
        f"\n[🧵 ПОТОК ЗАПУЩЕН] {current.name} (ID: {current.ident}) | Задача #{task_id}",
        flush=True,
    )

    # Имитация тяжёлой работы: отправка email, парсинг и т.д.
    time.sleep(2)

    print(
        f"[✅ ПОТОК ЗАВЕРШЕН] {current.name} | Задача #{task_id} обработана", flush=True
    )


@router.get("/", response_model=List[schemas.TaskResponse])
async def get_tasks(
    current_user: models.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    tasks = await crud.get_tasks(db, user_id=current_user.id)
    return tasks


@router.post("/", response_model=schemas.TaskResponse)
async def create_task(
    task_data: schemas.TaskCreate,
    current_user: models.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Сохраняем задачу в БД асинхронно (как у вас было)
    task = await crud.create_task(db, task_data, user_id=current_user.id)

    # ВЫНОСИМ СИНХРОННУЮ ОПЕРАЦИЮ В ОТДЕЛЬНЫЙ ПОТОК
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(
        thread_pool,  # Пул потоков
        heavy_background_task,  # Синхронная функция
        task.id,  # Аргументы
    )

    # Возвращаем ответ
    return task


@router.put("/{task_id}", response_model=schemas.TaskResponse)
async def update_task(
    task_id: int,
    task_update: schemas.TaskUpdate,
    current_user: models.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    task = await crud.update_task(db, task_id, current_user.id, task_update)
    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    return task


@router.delete("/{task_id}")
async def delete_task(
    task_id: int,
    current_user: models.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    deleted = await crud.delete_task(db, task_id, current_user.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    return {"message": "Задача удалена"}
