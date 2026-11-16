"""
Workflow Retry Policy, Exponential Backoff, and Dead-Letter Classification.
"""

import random
from typing import Optional


class RetryPolicy:
    """Configurable exponential backoff policy for workflow tasks."""

    def __init__(
        self,
        max_retries: int = 3,
        base_delay_seconds: float = 2.0,
        backoff_multiplier: float = 2.0,
        max_delay_seconds: float = 60.0,
        jitter_factor: float = 0.1,
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay_seconds
        self.multiplier = backoff_multiplier
        self.max_delay = max_delay_seconds
        self.jitter_factor = jitter_factor

    def compute_delay(self, retry_count: int) -> float:
        """Calculate wait seconds before next retry attempt."""
        delay = min(self.base_delay * (self.multiplier ** retry_count), self.max_delay)
        jitter = delay * self.jitter_factor * (random.random() * 2 - 1)
        return max(0.0, delay + jitter)

    def should_retry(self, current_retries: int, error_message: Optional[str] = None) -> bool:
        """Determine if another attempt is allowed."""
        if current_retries >= self.max_retries:
            return False
        if error_message and self.is_fatal_error(error_message):
            return False
        return True

    @staticmethod
    def is_fatal_error(error_message: str) -> bool:
        """Classify permanent errors that must not be blindly retried."""
        msg = error_message.lower()
        fatal_signatures = [
            "budget exceeded",
            "permission denied",
            "invalid project id",
            "production rejected",
            "invalid credentials",
            "authentication failed",
            "unauthorized",
        ]
        return any(sig in msg for sig in fatal_signatures)
