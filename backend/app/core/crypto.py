import base64
import hashlib
from cryptography.fernet import Fernet
from app.core.config import settings


def _get_fernet_key() -> bytes:
    """Derives a valid 32-byte urlsafe base64 key for Fernet from settings."""
    raw_key = settings.ENCRYPTION_KEY or "fallback-flagforge-dev-secret-key-32bytes"
    try:
        # Check if already a valid Fernet key
        decoded = base64.urlsafe_b64decode(raw_key.encode("utf-8"))
        if len(decoded) == 32:
            return raw_key.encode("utf-8")
    except Exception:
        pass
    # Derive deterministic 32-byte urlsafe base64 key via SHA256
    digest = hashlib.sha256(raw_key.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest)


def encrypt_secret(plain_text: str) -> str:
    """Encrypts a plaintext secret string using AES-128-CBC / Fernet."""
    if not plain_text:
        return ""
    key = _get_fernet_key()
    f = Fernet(key)
    return f.encrypt(plain_text.encode("utf-8")).decode("utf-8")


def decrypt_secret(cipher_text: str) -> str:
    """Decrypts an encrypted ciphertext secret string."""
    if not cipher_text:
        return ""
    key = _get_fernet_key()
    f = Fernet(key)
    try:
        return f.decrypt(cipher_text.encode("utf-8")).decode("utf-8")
    except Exception as e:
        raise ValueError(f"Failed to decrypt credential: {str(e)}")
