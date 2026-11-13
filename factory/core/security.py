"""
Security, Cryptography, and Secret Masking Utilities.
"""

import base64
import hashlib
from cryptography.fernet import Fernet
from factory.core.config import settings


def _get_fernet_instance() -> Fernet:
    """Ensure a valid 32-byte urlsafe base64 key is used for Fernet."""
    try:
        key_bytes = settings.ENCRYPTION_KEY.encode()
        return Fernet(key_bytes)
    except Exception:
        # Fallback to deterministic SHA-256 derived 32-byte urlsafe base64 key
        derived = base64.urlsafe_b64encode(hashlib.sha256(settings.SECRET_KEY.encode()).digest())
        return Fernet(derived)


def encrypt_secret(plain_text: str) -> str:
    """Encrypt a secret string at rest."""
    if not plain_text:
        return ""
    f = _get_fernet_instance()
    return f.encrypt(plain_text.encode()).decode()


def decrypt_secret(cipher_text: str) -> str:
    """Decrypt a secret string."""
    if not cipher_text:
        return ""
    f = _get_fernet_instance()
    return f.decrypt(cipher_text.encode()).decode()


def mask_secret(secret: str | None, unmasked_prefix: int = 4, unmasked_suffix: int = 4) -> str:
    """Mask sensitive tokens or keys for safe logging / display."""
    if not secret:
        return "<not-configured>"
    if len(secret) <= (unmasked_prefix + unmasked_suffix):
        return "****"
    return f"{secret[:unmasked_prefix]}****{secret[-unmasked_suffix:]}"


def hash_string(value: str) -> str:
    """Generate SHA-256 hash of a string."""
    return hashlib.sha256(value.encode()).hexdigest()
