"""
Unit tests for configuration and security cryptography.
"""

import pytest
from factory.core.config import settings
from factory.core.security import decrypt_secret, encrypt_secret, hash_string, mask_secret


def test_settings_loaded():
    assert settings.APP_NAME == "Autonomous AI Software Development Factory"
    assert settings.DEFAULT_EXECUTION_MODE == "autonomous"


def test_encryption_roundtrip():
    plain_text = "sk-super-secret-meta-api-token-12345"
    encrypted = encrypt_secret(plain_text)
    assert encrypted != plain_text
    decrypted = decrypt_secret(encrypted)
    assert decrypted == plain_text


def test_mask_secret():
    secret = "sk-proj-ABC12345678XYZ90"
    masked = mask_secret(secret, unmasked_prefix=4, unmasked_suffix=4)
    assert masked.startswith("sk-p")
    assert masked.endswith("YZ90")
    assert "****" in masked

    assert mask_secret(None) == "<not-configured>"
    assert mask_secret("short") == "****"


def test_hash_string():
    h1 = hash_string("test-string")
    h2 = hash_string("test-string")
    h3 = hash_string("different")
    assert h1 == h2
    assert h1 != h3
    assert len(h1) == 64
