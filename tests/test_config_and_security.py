"""
Unit tests for configuration and security cryptography.
"""

import pytest
from factory.api.routes import public_error_detail
from factory.core.config import (
    INSECURE_DEFAULT_ENCRYPTION_KEY,
    INSECURE_DEFAULT_SECRET_KEY,
    EnvironmentType,
    enforce_production_secrets,
    settings,
)
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


def test_production_refuses_published_secrets():
    with pytest.raises(RuntimeError):
        enforce_production_secrets(
            EnvironmentType.PRODUCTION,
            INSECURE_DEFAULT_SECRET_KEY,
            "custom-encryption-key",
        )
    enforce_production_secrets(
        EnvironmentType.TESTING,
        INSECURE_DEFAULT_SECRET_KEY,
        INSECURE_DEFAULT_ENCRYPTION_KEY,
    )


def test_production_rejects_invalid_fernet_key(monkeypatch):
    monkeypatch.setattr(settings, "ENVIRONMENT", EnvironmentType.PRODUCTION)
    monkeypatch.setattr(settings, "ENCRYPTION_KEY", "not-a-fernet-key")
    with pytest.raises(RuntimeError):
        encrypt_secret("value")


def test_internal_errors_are_hidden_unless_debug(monkeypatch):
    monkeypatch.setattr(settings, "DEBUG", False)
    assert public_error_detail(RuntimeError("token sk-live-example")) == "Internal server error"
    monkeypatch.setattr(settings, "DEBUG", True)
    assert "sk-live-example" in public_error_detail(RuntimeError("token sk-live-example"))


def test_hash_string():
    h1 = hash_string("test-string")
    h2 = hash_string("test-string")
    h3 = hash_string("different")
    assert h1 == h2
    assert h1 != h3
    assert len(h1) == 64
