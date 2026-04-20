from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import timedelta
import json

from app import schemas, models, crud
from app.database import get_db
from app.auth import (
    create_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    decode_access_token,
)
from app.dependencies import get_current_user
from app.utils import two_factor

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=schemas.UserResponse)
async def register(user_data: schemas.UserCreate, db: AsyncSession = Depends(get_db)):
    existing_user = await crud.get_user_by_email(db, user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким email уже существует",
        )

    user = await crud.create_user(db, user_data)
    return user


@router.post("/login")
async def login(login_data: schemas.UserLogin, db: AsyncSession = Depends(get_db)):
    """Вход — если включена 2FA, возвращает что нужен код"""
    user = await crud.authenticate_user(db, login_data.email, login_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Неверный email или пароль")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Аккаунт заблокирован")

    # Если 2FA включена — не даём токен сразу
    if user.otp_enabled:
        temp_token = create_access_token(
            data={"user_id": user.id, "email": user.email, "temp": True},
            expires_delta=timedelta(minutes=5),
        )
        return {
            "requires_2fa": True,
            "temp_token": temp_token,
            "user_id": user.id,
            "message": "Введите код из приложения",
        }

    # Обычный вход без 2FA
    access_token = create_access_token(
        data={"user_id": user.id, "email": user.email},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "requires_2fa": False,
        "user": schemas.UserResponse.model_validate(user),
    }


@router.post("/login/2fa")
async def login_2fa(
    request: schemas.TwoFactorLoginRequest, db: AsyncSession = Depends(get_db)
):
    user = await crud.get_user_by_email(db, request.email)
    if not user or not user.otp_enabled or not user.otp_secret:
        raise HTTPException(
            status_code=401, detail="Пользователь не найден или 2FA не активна"
        )

    # 🔹 1. Приводим ввод к единому виду
    clean_input = request.code.strip().replace(" ", "").replace("-", "").upper()

    # 🔹 2. Пробуем TOTP
    try:
        import pyotp

        is_totp_valid = pyotp.TOTP(user.otp_secret).verify(clean_input, valid_window=1)
    except Exception:
        is_totp_valid = False

    # 🔹 3. Проверяем резервные коды (если TOTP не подошёл)
    is_backup_used = False
    if not is_totp_valid and user.backup_codes:
        try:
            # Загружаем список из БД
            saved_codes = (
                json.loads(user.backup_codes)
                if isinstance(user.backup_codes, str)
                else user.backup_codes
            )

            # Приводим ВСЕ сохранённые коды к тому же виду, что и ввод
            normalized_saved = [
                c.strip().replace(" ", "").replace("-", "").upper() for c in saved_codes
            ]

            if clean_input in normalized_saved:
                # Находим индекс совпавшего кода и удаляем ОРИГИНАЛ из списка
                idx = normalized_saved.index(clean_input)
                saved_codes.pop(idx)
                user.backup_codes = json.dumps(saved_codes)
                is_backup_used = True
        except (json.JSONDecodeError, TypeError, ValueError, IndexError):
            pass

    # 🔹 4. Отказ, если ничего не подошло
    if not is_totp_valid and not is_backup_used:
        raise HTTPException(
            status_code=401, detail="Неверный код 2FA или резервный код уже использован"
        )

    # 🔹 5. Сохраняем в БД только при использовании резервного кода
    if is_backup_used:
        await db.commit()

    # 🔹 6. Выдаём токен
    access_token = create_access_token(
        data={"user_id": user.id, "email": user.email},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "requires_2fa": False,
        "user": schemas.UserResponse.model_validate(user),
    }


@router.post("/2fa/setup", response_model=schemas.TwoFactorSetupResponse)
async def setup_2fa(
    current_user: models.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Начать настройку 2FA — вернуть QR-код"""
    if current_user.otp_enabled:
        raise HTTPException(status_code=400, detail="2FA уже включена")

    secret = two_factor.generate_secret()
    uri = two_factor.get_totp_uri(secret, current_user.email)
    qr_code = two_factor.generate_qr_code_base64(uri)

    current_user.otp_secret = secret
    await db.commit()

    return schemas.TwoFactorSetupResponse(secret=secret, qr_code=qr_code, uri=uri)


@router.post("/2fa/enable")
async def enable_2fa(
    request: schemas.TwoFactorVerifyRequest,
    current_user: models.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Включить 2FA после проверки кода"""
    if current_user.otp_enabled:
        raise HTTPException(status_code=400, detail="2FA уже включена")

    if not current_user.otp_secret:
        raise HTTPException(status_code=400, detail="Сначала выполните /2fa/setup")

    if not two_factor.verify_code(current_user.otp_secret, request.code):
        raise HTTPException(status_code=400, detail="Неверный код")

    backup_codes = two_factor.generate_backup_codes()

    current_user.otp_enabled = True
    current_user.backup_codes = json.dumps(backup_codes)
    await db.commit()

    return {"message": "2FA успешно включена", "backup_codes": backup_codes}


@router.post("/2fa/disable")
async def disable_2fa(
    request: schemas.TwoFactorVerifyRequest,
    current_user: models.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Отключить 2FA"""
    if not current_user.otp_enabled:
        raise HTTPException(status_code=400, detail="2FA не включена")

    if not two_factor.verify_code(current_user.otp_secret, request.code):
        raise HTTPException(status_code=400, detail="Неверный код")

    current_user.otp_enabled = False
    current_user.otp_secret = None
    current_user.backup_codes = None
    await db.commit()

    return {"message": "2FA отключена"}
