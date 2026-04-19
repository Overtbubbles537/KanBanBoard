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
    """Второй этап входа — проверка 2FA кода"""
    user = await crud.get_user_by_email(db, request.email)
    if not user:
        raise HTTPException(status_code=401, detail="Пользователь не найден")

    if not user.otp_enabled or not user.otp_secret:
        raise HTTPException(status_code=400, detail="2FA не включена")

    # Проверяем код
    if not two_factor.verify_code(user.otp_secret, request.code):
        # Проверяем резервные коды
        if user.backup_codes:
            valid, new_codes = two_factor.verify_backup_code(
                user.backup_codes, request.code
            )
            if valid:
                user.backup_codes = json.dumps(new_codes)
                await db.commit()
            else:
                raise HTTPException(status_code=401, detail="Неверный код")
        else:
            raise HTTPException(status_code=401, detail="Неверный код")

    # Выдаём полноценный токен
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
