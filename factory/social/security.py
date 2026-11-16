"""
Social Integration Security, Webhook Verification, and Secret Sanitization.
Provides cryptographic validation for Meta, WhatsApp, X, and TikTok webhooks.
"""

import base64
import hashlib
import hmac
from typing import Any, Dict, Optional
from factory.core.logger import logger


def verify_meta_webhook_signature(payload_bytes: bytes, signature_header: str, app_secret: str) -> bool:
    """
    Verify Meta X-Hub-Signature-256 header (format: 'sha256=<hex_digest>').
    Prevents forged webhook deliveries.
    """
    if not signature_header or not app_secret:
        return False

    parts = signature_header.split("sha256=")
    if len(parts) != 2:
        return False
    expected_hash = parts[1].strip()

    computed = hmac.new(app_secret.encode("utf-8"), payload_bytes, hashlib.sha256).hexdigest()
    return hmac.compare_digest(computed, expected_hash)


def verify_meta_webhook_challenge(
    mode: Optional[str],
    token: Optional[str],
    challenge: Optional[str],
    expected_verify_token: str,
) -> Optional[str]:
    """
    Respond to Meta webhook subscription verification GET requests.
    Returns challenge string if authorized, or None if unauthorized.
    """
    if mode == "subscribe" and token == expected_verify_token:
        return challenge
    return None


def generate_twitter_crc_response(crc_token: str, consumer_secret: str) -> str:
    """
    Generate Twitter/X CRC (Challenge-Response Check) token.
    Format: 'sha256=' + base64_digest.
    """
    digest = hmac.new(consumer_secret.encode("utf-8"), crc_token.encode("utf-8"), hashlib.sha256).digest()
    b64_sig = base64.b64encode(digest).decode("utf-8")
    return f"sha256={b64_sig}"


def sanitize_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively redact sensitive keys from log dictionaries.
    """
    sensitive_keys = {
        "access_token",
        "refresh_token",
        "client_secret",
        "app_secret",
        "api_key",
        "api_secret",
        "password",
        "secret",
        "authorization",
    }
    sanitized = {}
    for k, v in payload.items():
        if k.lower() in sensitive_keys:
            sanitized[k] = "********"
        elif isinstance(v, dict):
            sanitized[k] = sanitize_payload(v)
        elif isinstance(v, list):
            sanitized[k] = [sanitize_payload(item) if isinstance(item, dict) else item for item in v]
        else:
            sanitized[k] = v
    return sanitized
