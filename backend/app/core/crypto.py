import base64
import hashlib
from cryptography.fernet import Fernet
from app.core.config import settings

WEBHOOK_SECRET_PREFIX = "ffenc:v1:"


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


def encrypt_webhook_secret(secret: str | None) -> str | None:
    """Encrypt a provider signing secret with an explicit version marker."""
    if not secret:
        return None
    return WEBHOOK_SECRET_PREFIX + encrypt_secret(secret)


def decrypt_webhook_secret(secret: str | None) -> str | None:
    """Decrypt protected webhook secrets and accept legacy plaintext during rollout."""
    if not secret:
        return None
    if secret.startswith(WEBHOOK_SECRET_PREFIX):
        return decrypt_secret(secret[len(WEBHOOK_SECRET_PREFIX):])
    # Transitional compatibility for rows created before migration 009.
    return secret
