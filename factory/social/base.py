"""
Social Platform Integration Base Types, Rate Limiting, and Audit Infrastructure.
"""

import time
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from factory.core.logger import logger
from factory.core.security import mask_secret


class SocialApiResult(BaseModel):
    """Unified result container for all social platform agent operations."""

    success: bool
    platform: str
    operation: str
    status_code: int = 200
    data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    error_code: Optional[str] = None
    rate_limit_remaining: Optional[int] = None
    rate_limit_reset_timestamp: Optional[int] = None
    latency_ms: int = 0
    evidence: Optional[str] = None


class PlatformCredentials(BaseModel):
    """Container for developer application and account credentials."""

    platform: str
    account_type: str = "customer"  # factory_owner, customer
    client_id: str
    client_secret: Optional[str] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_expires_at: Optional[float] = None
    granted_scopes: List[str] = Field(default_factory=list)
    redirect_uri: Optional[str] = None
    api_key: Optional[str] = None
    api_secret: Optional[str] = None

    def sanitized_dict(self) -> Dict[str, Any]:
        """Return safe representation with masked secrets."""
        return {
            "platform": self.platform,
            "account_type": self.account_type,
            "client_id": self.client_id,
            "has_client_secret": bool(self.client_secret),
            "access_token_masked": mask_secret(self.access_token),
            "has_refresh_token": bool(self.refresh_token),
            "token_expires_at": self.token_expires_at,
            "granted_scopes": self.granted_scopes,
            "redirect_uri": self.redirect_uri,
        }


class PlatformRateLimiter:
    """Sliding-window in-memory rate limiter per tenant & platform."""

    def __init__(self, max_requests: int = 200, window_seconds: int = 3600):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._history: Dict[str, List[float]] = {}

    def is_allowed(self, key: str) -> bool:
        now = time.time()
        requests = self._history.get(key, [])
        valid_requests = [t for t in requests if now - t < self.window_seconds]
        self._history[key] = valid_requests
        return len(valid_requests) < self.max_requests

    def record_request(self, key: str) -> int:
        now = time.time()
        if key not in self._history:
            self._history[key] = []
        self._history[key].append(now)
        remaining = max(0, self.max_requests - len(self._history[key]))
        return remaining

    def get_remaining(self, key: str) -> int:
        now = time.time()
        requests = self._history.get(key, [])
        valid = [t for t in requests if now - t < self.window_seconds]
        return max(0, self.max_requests - len(valid))
