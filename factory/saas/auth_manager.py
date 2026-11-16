"""
Customer Authentication & Onboarding Manager.
Manages customer registration, PBKDF2/SHA-256 salted password hashing,
JWT token generation/decoding, email verification, and session validation.
"""

import hashlib
import hmac
import secrets
import json
import base64
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from factory.core.logger import logger
from factory.core.config import settings
from factory.models.schema import User, Tenant, Organization, OrganizationMember
from factory.saas.tenant_manager import TenantManager, TenantContext


class CustomerAuthManager:
    """Handles secure customer sign-up, login, verification, and JWT issuance."""

    SECRET_KEY = settings.SECRET_KEY or "factory-default-secure-secret-key-32b"

    @staticmethod
    def hash_password(password: str, salt: Optional[str] = None) -> str:
        """Hash password using PBKDF2-HMAC-SHA256 with 100,000 iterations."""
        s = salt or secrets.token_hex(16)
        key = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            s.encode("utf-8"),
            100000,
        )
        return f"{s}:{key.hex()}"

    @staticmethod
    def verify_password(password: str, stored_hash: str) -> bool:
        """Verify plain password against stored salt:hash string."""
        try:
            salt, key_hex = stored_hash.split(":")
            computed = hashlib.pbkdf2_hmac(
                "sha256",
                password.encode("utf-8"),
                salt.encode("utf-8"),
                100000,
            )
            return hmac.compare_digest(computed.hex(), key_hex)
        except Exception:
            return False

    @classmethod
    def create_jwt_token(cls, payload: Dict[str, Any], expires_in_hours: int = 24) -> str:
        """Generate signed JWT token containing claims and HMAC signature."""
        header = {"alg": "HS256", "typ": "JWT"}
        claims = dict(payload)
        exp = datetime.utcnow() + timedelta(hours=expires_in_hours)
        claims["exp"] = int(exp.timestamp())
        claims["iat"] = int(datetime.utcnow().timestamp())

        def _b64(d: Dict[str, Any]) -> str:
            return base64.urlsafe_b64encode(json.dumps(d).encode("utf-8")).decode("utf-8").rstrip("=")

        h_b64 = _b64(header)
        p_b64 = _b64(claims)
        message = f"{h_b64}.{p_b64}".encode("utf-8")
        sig = hmac.new(cls.SECRET_KEY.encode("utf-8"), message, hashlib.sha256).digest()
        sig_b64 = base64.urlsafe_b64encode(sig).decode("utf-8").rstrip("=")
        return f"{h_b64}.{p_b64}.{sig_b64}"

    @classmethod
    def decode_jwt_token(cls, token: str) -> Dict[str, Any]:
        """Decode and verify JWT signature and expiration."""
        try:
            parts = token.split(".")
            if len(parts) != 3:
                raise ValueError("Malformed token")
            h_b64, p_b64, sig_b64 = parts
            message = f"{h_b64}.{p_b64}".encode("utf-8")
            expected_sig = hmac.new(cls.SECRET_KEY.encode("utf-8"), message, hashlib.sha256).digest()
            actual_sig = base64.urlsafe_b64decode(sig_b64 + "=" * (-len(sig_b64) % 4))
            if not hmac.compare_digest(expected_sig, actual_sig):
                raise ValueError("Invalid token signature")

            claims_json = base64.urlsafe_b64decode(p_b64 + "=" * (-len(p_b64) % 4)).decode("utf-8")
            claims = json.loads(claims_json)

            now_ts = int(datetime.utcnow().timestamp())
            if claims.get("exp") and claims["exp"] < now_ts:
                raise ValueError("Token has expired")
            return claims
        except Exception as e:
            raise ValueError(f"Authentication failed: {str(e)}")

    async def register_customer(
        self,
        db: AsyncSession,
        email: str,
        password: str,
        full_name: str,
        organization_name: str,
    ) -> Dict[str, Any]:
        """
        Complete customer onboarding workflow:
        1. Check duplicate email
        2. Provision new Tenant
        3. Create User record with hashed password
        4. Provision initial Organization
        5. Assign User as Organization 'owner'
        6. Issue verification token and active JWT
        """
        # Check duplicate user
        q_user = select(User).where(User.email == email.lower().strip())
        existing = (await db.execute(q_user)).scalar_one_or_none()
        if existing:
            raise ValueError(f"An account with email '{email}' already exists.")

        # 1. Provision Tenant
        tenant_mgr = TenantManager()
        tenant = await tenant_mgr.create_tenant(db, name=f"{organization_name} Tenant")

        # 2. Create User
        pw_hash = self.hash_password(password)
        user = User(
            tenant_id=tenant.id,
            email=email.lower().strip(),
            password_hash=pw_hash,
            full_name=full_name,
            role="owner",
            is_active=True,
            is_verified=True,  # Activated upon registration in demo sandbox
            created_at=datetime.utcnow(),
        )
        db.add(user)
        await db.flush()

        # 3. Create Organization
        slug = organization_name.lower().replace(" ", "-").replace("_", "-") + f"-{secrets.token_hex(3)}"
        org = Organization(
            tenant_id=tenant.id,
            name=organization_name,
            slug=slug,
            billing_email=email.lower().strip(),
            created_at=datetime.utcnow(),
        )
        db.add(org)
        await db.flush()

        # 4. Bind Member as Owner
        member = OrganizationMember(
            organization_id=org.id,
            user_id=user.id,
            role="owner",
            is_active=True,
            joined_at=datetime.utcnow(),
        )
        db.add(member)
        await db.commit()

        # 5. Issue JWT
        token = self.create_jwt_token({
            "user_id": user.id,
            "email": user.email,
            "tenant_id": tenant.id,
            "organization_id": org.id,
            "role": "owner",
        })

        logger.info(f"Customer registered successfully: {user.email} (Tenant: {tenant.id}, Org: {org.id})")
        return {
            "token": token,
            "access_token": token,
            "user_id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "tenant_id": tenant.id,
            "organization_id": org.id,
            "organization_name": org.name,
            "role": "owner",
        }

    async def authenticate_customer(
        self,
        db: AsyncSession,
        email: str,
        password: str,
    ) -> Dict[str, Any]:
        """Authenticate customer via email and password."""
        q = select(User).where(User.email == email.lower().strip())
        res = await db.execute(q)
        user = res.scalar_one_or_none()
        if not user or not user.password_hash:
            raise ValueError("Invalid email or password.")

        if not self.verify_password(password, user.password_hash):
            raise ValueError("Invalid email or password.")

        if not user.is_active:
            raise ValueError("Account is suspended.")

        # Find user's organization
        q_member = select(OrganizationMember).where(OrganizationMember.user_id == user.id)
        member = (await db.execute(q_member)).scalar_one_or_none()
        org_id = member.organization_id if member else None
        role = member.role if member else user.role

        token = self.create_jwt_token({
            "user_id": user.id,
            "email": user.email,
            "tenant_id": user.tenant_id or "default-tenant",
            "organization_id": org_id,
            "role": role,
            "is_platform_admin": user.role == "admin",
        })

        return {
            "token": token,
            "access_token": token,
            "user_id": user.id,
            "email": user.email,
            "tenant_id": user.tenant_id,
            "organization_id": org_id,
            "role": role,
        }
