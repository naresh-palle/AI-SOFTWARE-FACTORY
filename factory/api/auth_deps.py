"""
Shared authentication dependencies for operator and customer Studio access.
"""

from __future__ import annotations

import secrets
from typing import Any, Dict, Optional

from fastapi import Header, HTTPException, status

from factory.core.config import EnvironmentType, settings
from factory.saas.auth_manager import CustomerAuthManager


def _constant_time_equal(provided: str, expected: str) -> bool:
    try:
        return secrets.compare_digest(provided.encode("utf-8"), expected.encode("utf-8"))
    except Exception:
        return False


def _bearer_token(authorization: Optional[str]) -> Optional[str]:
    if not authorization:
        return None
    if authorization.startswith("Bearer "):
        return authorization[7:].strip()
    return None


def is_operator_bearer(authorization: Optional[str]) -> bool:
    configured = settings.FACTORY_API_TOKEN or ""
    if not configured:
        return False
    return _constant_time_equal(authorization or "", f"Bearer {configured}")


def require_operator_token(authorization: Optional[str] = Header(default=None)) -> None:
    """Protect operator routes when a token is configured, and always in production."""
    configured = settings.FACTORY_API_TOKEN or ""
    if settings.ENVIRONMENT == EnvironmentType.PRODUCTION and not configured:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Operator authentication is not configured",
        )
    if not configured:
        return
    if not is_operator_bearer(authorization):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")


def require_api_access(authorization: Optional[str] = Header(default=None)) -> None:
    """
    Gate for /api/v1 orchestration routes.
    Accepts FACTORY_API_TOKEN (operator) or a valid customer Studio JWT.
    """
    if is_operator_bearer(authorization):
        return

    token = _bearer_token(authorization)
    if token:
        try:
            CustomerAuthManager.decode_jwt_token(token)
            return
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token: {exc}",
            ) from exc

    require_operator_token(authorization)


def require_platform_admin(
    authorization: Optional[str] = Header(default=None),
) -> Dict[str, Any]:
    """
    Protect SaaS administration endpoints.
    Accepts FACTORY_API_TOKEN (operator) or a customer JWT with is_platform_admin=true.
    """
    if is_operator_bearer(authorization):
        return {
            "auth_type": "operator",
            "is_platform_admin": True,
            "user_id": "operator",
            "role": "admin",
        }

    token = _bearer_token(authorization)
    if token:
        try:
            claims = CustomerAuthManager.decode_jwt_token(token)
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token: {exc}",
            ) from exc
        if claims.get("is_platform_admin") or claims.get("role") == "admin":
            claims = dict(claims)
            claims["auth_type"] = "platform_admin"
            claims["is_platform_admin"] = True
            return claims

    # Local/dev convenience only when no operator token is configured.
    if (
        settings.ENVIRONMENT in (EnvironmentType.DEVELOPMENT, EnvironmentType.TESTING)
        and not (settings.FACTORY_API_TOKEN or "")
    ):
        return {
            "auth_type": "dev_open",
            "is_platform_admin": True,
            "user_id": "dev-admin",
            "role": "admin",
        }

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Platform administrator authentication required",
    )


def resolve_studio_auth(
    authorization: Optional[str] = Header(default=None),
    x_tenant_id: Optional[str] = Header(default=None),
) -> Dict[str, Any]:
    """
    Resolve Studio/project API auth.
    Priority: operator token → customer JWT → testing header (explicitly enabled) →
    open local operator (non-production, no token configured).
    """
    if is_operator_bearer(authorization):
        return {
            "auth_type": "operator",
            "is_platform_admin": True,
            "tenant_id": None,
            "user_id": "operator",
            "role": "admin",
        }

    token = _bearer_token(authorization)
    if token:
        try:
            claims = CustomerAuthManager.decode_jwt_token(token)
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token: {exc}",
            ) from exc
        claims = dict(claims)
        claims["auth_type"] = "customer"
        claims["is_platform_admin"] = bool(
            claims.get("is_platform_admin") or claims.get("role") == "admin"
        )
        if not claims.get("tenant_id"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token missing tenant context",
            )
        return claims

    if x_tenant_id and settings.ALLOW_TENANT_HEADER_AUTH:
        if settings.ENVIRONMENT not in (EnvironmentType.TESTING, EnvironmentType.DEVELOPMENT):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Tenant header auth is disabled",
            )
        return {
            "auth_type": "tenant_header",
            "tenant_id": x_tenant_id,
            "user_id": "test_user_id",
            "email": "system@tenant.local",
            "role": "owner",
            "is_platform_admin": False,
        }

    configured = settings.FACTORY_API_TOKEN or ""
    if settings.ENVIRONMENT == EnvironmentType.PRODUCTION:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization credentials",
        )
    if configured:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
        )

    # Non-production with no operator token: preserve local dashboard ergonomics.
    return {
        "auth_type": "dev_open",
        "tenant_id": None,
        "user_id": None,
        "role": "operator",
        "is_platform_admin": True,
    }


def extract_saas_auth_context(
    authorization: Optional[str],
    x_tenant_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Customer SaaS routes: JWT required; tenant header only when explicitly allowed."""
    token = _bearer_token(authorization)
    if token:
        try:
            return CustomerAuthManager.decode_jwt_token(token)
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token: {exc}",
            ) from exc

    if x_tenant_id and settings.ALLOW_TENANT_HEADER_AUTH:
        if settings.ENVIRONMENT not in (EnvironmentType.TESTING, EnvironmentType.DEVELOPMENT):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Tenant header auth is disabled",
            )
        return {
            "tenant_id": x_tenant_id,
            "user_id": "test_user_id",
            "email": "system@tenant.local",
            "role": "owner",
        }

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Missing authorization credentials",
    )
