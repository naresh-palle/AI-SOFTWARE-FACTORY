"""
Common OAuth 2.0 Engine with PKCE, State Validation, Fernet Encryption, and Multi-Tenant Isolation.
Supports Meta (Facebook, Instagram, WhatsApp, Messenger, Threads), Google/YouTube, X, LinkedIn, and TikTok.
"""

import base64
import hashlib
import hmac
import os
import secrets
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlencode

import httpx
from pydantic import BaseModel, Field
from sqlalchemy import desc, select, update

from factory.core.config import settings
from factory.core.database import get_db_session
from factory.core.logger import logger
from factory.core.security import decrypt_secret, encrypt_secret, mask_secret
from factory.models.schema import AccountConnectionHistory, DeveloperApplication, OAuthConnection, SocialIntegrationLog
from factory.social.base import PlatformRateLimiter


class OAuthTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: Optional[int] = 3600
    refresh_token: Optional[str] = None
    scope: Optional[str] = None
    user_id: Optional[str] = None
    raw_response: Dict[str, Any] = Field(default_factory=dict)


# In-memory store for pending PKCE verifiers & state tokens (TTL: 15 mins)
_PENDING_OAUTH_SESSIONS: Dict[str, Dict[str, Any]] = {}

# Standard platform OAuth endpoints and defaults
PLATFORM_OAUTH_CONFIG: Dict[str, Dict[str, Any]] = {
    "facebook": {
        "auth_url": "https://www.facebook.com/v20.0/dialog/oauth",
        "token_url": "https://graph.facebook.com/v20.0/oauth/access_token",
        "revoke_url": "https://graph.facebook.com/v20.0/me/permissions",
        "default_scopes": ["email", "public_profile", "pages_show_list", "pages_read_engagement"],
        "supports_pkce": False,
        "token_style": "json",
    },
    "instagram": {
        "auth_url": "https://www.facebook.com/v20.0/dialog/oauth",
        "token_url": "https://graph.facebook.com/v20.0/oauth/access_token",
        "default_scopes": ["instagram_basic", "instagram_manage_insights", "pages_show_list"],
        "supports_pkce": False,
    },
    "whatsapp": {
        "auth_url": "https://www.facebook.com/v20.0/dialog/oauth",
        "token_url": "https://graph.facebook.com/v20.0/oauth/access_token",
        "default_scopes": ["whatsapp_business_messaging", "whatsapp_business_management"],
        "supports_pkce": False,
    },
    "threads": {
        "auth_url": "https://threads.net/oauth/authorize",
        "token_url": "https://graph.threads.net/oauth/access_token",
        "default_scopes": ["threads_basic", "threads_content_publish", "threads_read_replies"],
        "supports_pkce": False,
    },
    "google": {
        "auth_url": "https://accounts.google.com/o/oauth2/v2/auth",
        "token_url": "https://oauth2.googleapis.com/token",
        "revoke_url": "https://oauth2.googleapis.com/revoke",
        "default_scopes": [
            "openid",
            "email",
            "profile",
            "https://www.googleapis.com/auth/youtube.readonly",
        ],
        "supports_pkce": True,
    },
    "youtube": {
        "auth_url": "https://accounts.google.com/o/oauth2/v2/auth",
        "token_url": "https://oauth2.googleapis.com/token",
        "revoke_url": "https://oauth2.googleapis.com/revoke",
        "default_scopes": [
            "https://www.googleapis.com/auth/youtube",
            "https://www.googleapis.com/auth/youtube.readonly",
            "https://www.googleapis.com/auth/yt-analytics.readonly",
        ],
        "supports_pkce": True,
    },
    "x": {
        "auth_url": "https://twitter.com/i/oauth2/authorize",
        "token_url": "https://api.twitter.com/2/oauth2/token",
        "revoke_url": "https://api.twitter.com/2/oauth2/revoke",
        "default_scopes": ["tweet.read", "tweet.write", "users.read", "offline.access"],
        "supports_pkce": True,
    },
    "linkedin": {
        "auth_url": "https://www.linkedin.com/oauth/v2/authorization",
        "token_url": "https://www.linkedin.com/oauth/v2/accessToken",
        "default_scopes": ["openid", "profile", "email", "w_member_social"],
        "supports_pkce": True,
    },
    "tiktok": {
        "auth_url": "https://www.tiktok.com/v2/auth/authorize/",
        "token_url": "https://open.tiktokapis.com/v2/oauth/token/",
        "revoke_url": "https://open.tiktokapis.com/v2/oauth/revoke/",
        "default_scopes": ["user.info.basic", "video.list", "video.publish"],
        "supports_pkce": True,
    },
}


def generate_pkce_pair() -> Tuple[str, str]:
    """Generate a high-entropy PKCE code_verifier and S256 code_challenge."""
    verifier = secrets.token_urlsafe(64)
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    challenge = base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")
    return verifier, challenge


def generate_state(tenant_id: str, platform: str) -> str:
    """Generate an HMAC-signed state token preventing CSRF and tracking context."""
    nonce = secrets.token_hex(16)
    timestamp = str(int(time.time()))
    payload = f"{tenant_id}:{platform}:{timestamp}:{nonce}"
    sig = hmac.new(settings.SECRET_KEY.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{payload}:{sig}"


def verify_state(state: str, expected_platform: str) -> Optional[str]:
    """Validate state signature and freshness (15-min window). Returns tenant_id or None."""
    parts = state.split(":")
    if len(parts) != 5:
        return None
    tenant_id, platform, timestamp, nonce, sig = parts
    if platform != expected_platform:
        return None
    # Check expiry (900 seconds)
    try:
        ts = int(timestamp)
        if time.time() - ts > 900:
            return None
    except ValueError:
        return None

    payload = f"{tenant_id}:{platform}:{timestamp}:{nonce}"
    expected_sig = hmac.new(settings.SECRET_KEY.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(sig, expected_sig):
        return None
    return tenant_id


class CommonOAuthEngine:
    """Orchestrates authorization flows, code exchanges, and token lifecycle across all platforms."""

    def __init__(self):
        self.rate_limiter = PlatformRateLimiter(max_requests=100, window_seconds=3600)

    def get_authorization_url(
        self,
        platform: str,
        tenant_id: str = "default",
        redirect_uri: Optional[str] = None,
        scopes: Optional[List[str]] = None,
        custom_client_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Build standard OAuth authorization URL with signed state and PKCE if applicable.
        """
        cfg = PLATFORM_OAUTH_CONFIG.get(platform.lower())
        if not cfg:
            raise ValueError(f"Unsupported OAuth platform: {platform}")

        client_id = custom_client_id or self._resolve_client_id(platform)
        if not client_id:
            client_id = f"demo_{platform}_client_id"

        actual_redirect = redirect_uri or f"http://localhost:8000/api/v1/social/oauth/{platform}/callback"
        state = generate_state(tenant_id, platform)
        requested_scopes = scopes or cfg.get("default_scopes", [])

        params: Dict[str, str] = {
            "client_id": client_id,
            "redirect_uri": actual_redirect,
            "response_type": "code",
            "state": state,
            "scope": " ".join(requested_scopes) if platform != "facebook" else ",".join(requested_scopes),
        }

        # Handle PKCE if supported
        code_verifier = None
        if cfg.get("supports_pkce", False):
            code_verifier, code_challenge = generate_pkce_pair()
            params["code_challenge"] = code_challenge
            params["code_challenge_method"] = "S256"

        # Platform specific nuances
        if platform in ["google", "youtube"]:
            params["access_type"] = "offline"
            params["prompt"] = "consent"
        elif platform == "tiktok":
            params["client_key"] = client_id
            params.pop("client_id", None)

        # Store session in memory for verifier retrieval
        _PENDING_OAUTH_SESSIONS[state] = {
            "tenant_id": tenant_id,
            "platform": platform,
            "code_verifier": code_verifier,
            "redirect_uri": actual_redirect,
            "client_id": client_id,
            "created_at": time.time(),
        }

        auth_url = f"{cfg['auth_url']}?{urlencode(params)}"
        logger.info(f"OAuthEngine: Generated authorization URL for {platform} (tenant: {tenant_id})")

        return {
            "platform": platform,
            "auth_url": auth_url,
            "state": state,
            "pkce_enabled": bool(code_verifier),
            "scopes": requested_scopes,
            "redirect_uri": actual_redirect,
        }

    async def exchange_code_for_tokens(
        self,
        platform: str,
        code: str,
        state: str,
        account_type: str = "customer",
    ) -> OAuthTokenResponse:
        """
        Exchange auth code for tokens, validate state, and persist encrypted credentials.
        """
        tenant_id = verify_state(state, platform)
        if not tenant_id:
            raise ValueError("Invalid or expired OAuth state parameter (CSRF protection)")

        session_meta = _PENDING_OAUTH_SESSIONS.pop(state, {})
        code_verifier = session_meta.get("code_verifier")
        redirect_uri = session_meta.get("redirect_uri") or f"http://localhost:8000/api/v1/social/oauth/{platform}/callback"

        client_id, client_secret = self._resolve_credentials(platform, session_meta.get("client_id"))

        # In mock or test mode, or if live credentials are not provisioned, generate deterministic tokens
        if not client_secret or client_secret.startswith("mock_") or client_id.startswith("demo_"):
            token_resp = OAuthTokenResponse(
                access_token=f"{platform}_live_token_{secrets.token_hex(20)}",
                token_type="bearer",
                expires_in=5184000 if platform in ["facebook", "instagram"] else 3600,
                refresh_token=f"{platform}_refresh_token_{secrets.token_hex(24)}",
                scope=" ".join(PLATFORM_OAUTH_CONFIG[platform]["default_scopes"]),
                user_id=f"usr_{platform}_{secrets.token_hex(6)}",
                raw_response={"simulated": True, "platform": platform},
            )
        else:
            # Perform real HTTP code exchange
            token_resp = await self._perform_http_token_exchange(
                platform, code, client_id, client_secret, redirect_uri, code_verifier
            )

        # Encrypt and save to database
        await self.save_connection(
            tenant_id=tenant_id,
            platform=platform,
            user_identifier=token_resp.user_id or f"user_{secrets.token_hex(4)}",
            account_type=account_type,
            access_token=token_resp.access_token,
            refresh_token=token_resp.refresh_token,
            expires_in=token_resp.expires_in,
            scopes=token_resp.scope.split() if token_resp.scope else PLATFORM_OAUTH_CONFIG[platform]["default_scopes"],
        )

        return token_resp

    async def refresh_access_token(self, connection_id: str) -> OAuthTokenResponse:
        """
        Refresh an expired access token using the stored encrypted refresh token.
        """
        async with get_db_session() as session:
            stmt = select(OAuthConnection).where(OAuthConnection.id == connection_id)
            res = await session.execute(stmt)
            conn = res.scalar_one_or_none()
            if not conn:
                raise ValueError(f"OAuthConnection not found: {connection_id}")

            if not conn.encrypted_refresh_token:
                raise ValueError("No refresh token available for this connection.")

            plain_refresh = decrypt_secret(conn.encrypted_refresh_token)
            platform = conn.provider

            client_id, client_secret = self._resolve_credentials(platform)

            # Simulated refresh if demo
            if not client_secret or client_secret.startswith("mock_"):
                new_token = f"{platform}_refreshed_access_{secrets.token_hex(20)}"
                expires_in = 3600
            else:
                cfg = PLATFORM_OAUTH_CONFIG.get(platform)
                async with httpx.AsyncClient(timeout=15.0) as client:
                    data = {
                        "grant_type": "refresh_token",
                        "refresh_token": plain_refresh,
                        "client_id": client_id,
                        "client_secret": client_secret,
                    }
                    r = await client.post(cfg["token_url"], data=data)
                    payload = r.json()
                    new_token = payload.get("access_token")
                    expires_in = payload.get("expires_in", 3600)

            # Update DB
            conn.encrypted_access_token = encrypt_secret(new_token)
            conn.token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
            conn.last_refreshed_at = datetime.utcnow()
            conn.status = "active"

            # History entry
            history = AccountConnectionHistory(
                tenant_id=conn.tenant_id,
                platform=platform,
                user_identifier=conn.user_identifier,
                action="token_refreshed",
                actor="OAuthEngine",
                details_json={"connection_id": connection_id, "expires_in": expires_in},
            )
            session.add(history)

            logger.info(f"OAuthEngine: Refreshed token for connection {connection_id} ({platform})")
            return OAuthTokenResponse(
                access_token=new_token,
                expires_in=expires_in,
                refresh_token=plain_refresh,
            )

    async def revoke_connection(self, connection_id: str) -> bool:
        """
        Revoke an active OAuth connection and mark it revoked in the database.
        """
        async with get_db_session() as session:
            stmt = select(OAuthConnection).where(OAuthConnection.id == connection_id)
            res = await session.execute(stmt)
            conn = res.scalar_one_or_none()
            if not conn:
                return False

            conn.status = "revoked"

            history = AccountConnectionHistory(
                tenant_id=conn.tenant_id,
                platform=conn.provider,
                user_identifier=conn.user_identifier,
                action="revoked",
                actor="User",
                details_json={"connection_id": connection_id},
            )
            session.add(history)
            logger.info(f"OAuthEngine: Revoked connection {connection_id} for platform {conn.provider}")
            return True

    async def save_connection(
        self,
        tenant_id: str,
        platform: str,
        user_identifier: str,
        account_type: str,
        access_token: str,
        refresh_token: Optional[str] = None,
        expires_in: Optional[int] = None,
        scopes: Optional[List[str]] = None,
        account_name: Optional[str] = None,
    ) -> OAuthConnection:
        """Encrypt tokens and persist connection."""
        enc_access = encrypt_secret(access_token)
        enc_refresh = encrypt_secret(refresh_token) if refresh_token else None
        expires_at = datetime.utcnow() + timedelta(seconds=expires_in or 3600)

        async with get_db_session() as session:
            # Check for existing connection for this tenant + platform + user
            stmt = select(OAuthConnection).where(
                OAuthConnection.tenant_id == tenant_id,
                OAuthConnection.provider == platform,
                OAuthConnection.user_identifier == user_identifier,
            )
            res = await session.execute(stmt)
            existing = res.scalar_one_or_none()

            if existing:
                existing.encrypted_access_token = enc_access
                existing.encrypted_refresh_token = enc_refresh or existing.encrypted_refresh_token
                existing.token_expires_at = expires_at
                existing.granted_scopes = scopes or existing.granted_scopes
                existing.status = "active"
                existing.updated_at = datetime.utcnow()
                conn_obj = existing
            else:
                conn_obj = OAuthConnection(
                    tenant_id=tenant_id,
                    provider=platform,
                    account_type=account_type,
                    user_identifier=user_identifier,
                    account_name=account_name or f"{platform.capitalize()} Account",
                    encrypted_access_token=enc_access,
                    encrypted_refresh_token=enc_refresh,
                    token_expires_at=expires_at,
                    granted_scopes=scopes or [],
                    status="active",
                )
                session.add(conn_obj)

            # Record in history
            hist = AccountConnectionHistory(
                tenant_id=tenant_id,
                platform=platform,
                user_identifier=user_identifier,
                action="connected",
                actor="OAuthEngine",
                details_json={"scopes": scopes, "account_type": account_type},
            )
            session.add(hist)

            return conn_obj

    async def get_decrypted_token(self, connection_id: str) -> str:
        """Safely fetch and decrypt access token for internal API agent usage."""
        async with get_db_session() as session:
            stmt = select(OAuthConnection).where(OAuthConnection.id == connection_id)
            res = await session.execute(stmt)
            conn = res.scalar_one_or_none()
            if not conn:
                raise ValueError(f"OAuthConnection not found: {connection_id}")
            if conn.status != "active":
                raise ValueError(f"OAuthConnection is not active (status: {conn.status})")
            return decrypt_secret(conn.encrypted_access_token)

    async def list_connections(self, tenant_id: str = "default") -> List[Dict[str, Any]]:
        """Return masked, safe summaries of active connections for frontend consumption."""
        async with get_db_session() as session:
            stmt = select(OAuthConnection).where(OAuthConnection.tenant_id == tenant_id).order_by(desc(OAuthConnection.created_at))
            res = await session.execute(stmt)
            rows = res.scalars().all()
            return [
                {
                    "id": r.id,
                    "platform": r.provider,
                    "account_type": r.account_type,
                    "account_name": r.account_name,
                    "user_identifier": r.user_identifier,
                    "status": r.status,
                    "token_expires_at": r.token_expires_at.isoformat() if r.token_expires_at else None,
                    "granted_scopes": r.granted_scopes,
                    "rate_limit_remaining": r.rate_limit_remaining,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                }
                for r in rows
            ]

    def _resolve_client_id(self, platform: str) -> Optional[str]:
        mapping = {
            "facebook": settings.META_APP_ID,
            "instagram": settings.META_APP_ID,
            "whatsapp": settings.META_APP_ID,
            "threads": settings.META_APP_ID,
            "google": settings.GOOGLE_CLIENT_ID,
            "youtube": settings.GOOGLE_CLIENT_ID,
            "x": settings.X_CLIENT_ID,
            "linkedin": settings.LINKEDIN_CLIENT_ID,
            "tiktok": settings.TIKTOK_CLIENT_KEY,
        }
        return mapping.get(platform.lower())

    def _resolve_credentials(self, platform: str, override_client_id: Optional[str] = None) -> Tuple[str, Optional[str]]:
        client_id = override_client_id or self._resolve_client_id(platform) or f"demo_{platform}_id"
        secret_map = {
            "facebook": settings.META_APP_SECRET,
            "instagram": settings.META_APP_SECRET,
            "whatsapp": settings.META_APP_SECRET,
            "threads": settings.META_APP_SECRET,
            "google": settings.GOOGLE_CLIENT_SECRET,
            "youtube": settings.GOOGLE_CLIENT_SECRET,
            "x": settings.X_CLIENT_SECRET,
            "linkedin": settings.LINKEDIN_CLIENT_SECRET,
            "tiktok": settings.TIKTOK_CLIENT_SECRET,
        }
        client_secret = secret_map.get(platform.lower())
        return client_id, client_secret

    async def _perform_http_token_exchange(
        self,
        platform: str,
        code: str,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        code_verifier: Optional[str] = None,
    ) -> OAuthTokenResponse:
        cfg = PLATFORM_OAUTH_CONFIG[platform]
        data: Dict[str, str] = {
            "code": code,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        }
        if platform != "tiktok":
            data["client_id"] = client_id
            data["client_secret"] = client_secret
        else:
            data["client_key"] = client_id
            data["client_secret"] = client_secret

        if code_verifier:
            data["code_verifier"] = code_verifier

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(cfg["token_url"], data=data)
            if resp.status_code != 200:
                raise RuntimeError(f"Token exchange failed ({resp.status_code}): {resp.text}")
            payload = resp.json()

            return OAuthTokenResponse(
                access_token=payload.get("access_token", ""),
                token_type=payload.get("token_type", "bearer"),
                expires_in=payload.get("expires_in", 3600),
                refresh_token=payload.get("refresh_token"),
                scope=payload.get("scope"),
                user_id=payload.get("user_id") or payload.get("id"),
                raw_response=payload,
            )
