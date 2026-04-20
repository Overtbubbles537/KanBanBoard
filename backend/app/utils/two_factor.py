import pyotp
import qrcode
import base64
from io import BytesIO
import json
import secrets
from typing import List, Tuple


def generate_secret() -> str:
    """Генерирует секретный ключ для 2FA"""
    return pyotp.random_base32()


def get_totp_uri(secret: str, email: str, issuer: str = "KanbanBoard") -> str:
    """Создаёт URI для добавления в TOTP"""
    totp = pyotp.TOTP(secret)
    return totp.provisioning_uri(name=email, issuer_name=issuer)


def generate_qr_code_base64(uri: str) -> str:
    """Создаёт QR-код и возвращает его как base64 строку"""
    qr = qrcode.make(uri)
    buffer = BytesIO()
    qr.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode()


def verify_code(secret: str, code: str) -> bool:
    """Проверяет одноразовый код"""
    totp = pyotp.TOTP(secret)
    return totp.verify(code)


def generate_backup_codes(count: int = 8) -> List[str]:
    """Генерирует резервные коды (по 8 символов)"""
    return [secrets.token_hex(4) for _ in range(count)]


def hash_backup_codes(codes: List[str]) -> str:
    """Превращает список кодов в JSON строку (в реальном проекте нужно хешировать)"""
    return json.dumps(codes)


def verify_backup_code(stored_codes: str, code: str) -> Tuple[bool, List[str]]:
    """Проверяет резервный код и удаляет его из списка"""
    codes = json.loads(stored_codes)
    if code in codes:
        codes.remove(code)
        return True, codes
    return False, codes
