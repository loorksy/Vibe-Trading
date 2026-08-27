import base64
import hashlib
from cryptography.fernet import Fernet

from app.config import get_settings


def _fernet() -> Fernet:
    settings = get_settings()
    key = settings.credentials_encryption_key
    if not key:
        # Derive deterministic dev key from app secret
        digest = hashlib.sha256(settings.app_secret_key.encode()).digest()
        key = base64.urlsafe_b64encode(digest)
    return Fernet(key if isinstance(key, bytes) else key.encode())


def encrypt_value(plain: str) -> str:
    return _fernet().encrypt(plain.encode()).decode()


def decrypt_value(cipher: str) -> str:
    return _fernet().decrypt(cipher.encode()).decode()
