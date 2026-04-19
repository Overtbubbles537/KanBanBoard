import pyotp
from typing import Optional, Tuple
import base64


def generate_otp_secret() -> str:
    """Сгенерировать секретный ключ для 2FA"""
    return pyotp.random_base32()


def get_otp_uri(secret: str, email: str, issuer: str = "KanbanBoard") -> str:
    """Получить URI для QR-кода (используется в Google Authenticator)"""
    return pyotp.totp.TOTP(secret).provisioning_uri(name=email, issuer_name=issuer)


def verify_otp_code(secret: str, code: str) -> bool:
    """Проверить одноразовый код"""
    totp = pyotp.TOTP(secret)
    return totp.verify(code)


def generate_backup_codes(count: int = 8) -> list[str]:
    """Сгенерировать резервные коды"""
    import secrets

    return [secrets.token_hex(4) for _ in range(count)]
