"""
Model Provider & Customer Integration Credential Manager
Manages LLM provider catalog, token pricing, and tenant-isolated encrypted third-party credentials.
"""

from __future__ import annotations

import base64
import hashlib
import os
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from cryptography.fernet import Fernet
from sqlalchemy import select, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from factory.models.schema import ModelProviderRecord, CustomerIntegrationCredential

ENCRYPTION_MASTER_KEY = os.getenv("SAAS_ENCRYPTION_KEY", "factory-saas-credential-master-key-32b-secret!")

def _get_fernet_cipher() -> Fernet:
    key_bytes = hashlib.sha256(ENCRYPTION_MASTER_KEY.encode()).digest()
    url_safe_key = base64.urlsafe_b64encode(key_bytes)
    return Fernet(url_safe_key)


DEFAULT_PROVIDERS = [
    {
        "provider": "openai",
        "model_name": "gpt-4o",
        "input_cost_per_1k": 0.005,
        "output_cost_per_1k": 0.015,
    },
    {
        "provider": "openai",
        "model_name": "gpt-4o-mini",
        "input_cost_per_1k": 0.00015,
        "output_cost_per_1k": 0.0006,
    },
    {
        "provider": "anthropic",
        "model_name": "claude-3-5-sonnet",
        "input_cost_per_1k": 0.003,
        "output_cost_per_1k": 0.015,
    },
    {
        "provider": "anthropic",
        "model_name": "claude-3-haiku",
        "input_cost_per_1k": 0.00025,
        "output_cost_per_1k": 0.00125,
    },
    {
        "provider": "google",
        "model_name": "gemini-1.5-pro",
        "input_cost_per_1k": 0.0035,
        "output_cost_per_1k": 0.0105,
    },
    {
        "provider": "google",
        "model_name": "gemini-1.5-flash",
        "input_cost_per_1k": 0.000075,
        "output_cost_per_1k": 0.0003,
    },
]


class ModelCatalogManager:
    """Manages AI model providers and token cost computation."""

    @staticmethod
    async def seed_default_providers(db: AsyncSession) -> List[ModelProviderRecord]:
        created = False
        for p in DEFAULT_PROVIDERS:
            q = select(ModelProviderRecord).where(
                and_(
                    ModelProviderRecord.provider_name == p["provider"],
                    ModelProviderRecord.model_name == p["model_name"]
                )
            )
            existing = (await db.execute(q)).scalar_one_or_none()
            if not existing:
                record = ModelProviderRecord(
                    id=str(uuid.uuid4()),
                    provider_name=p["provider"],
                    model_name=p["model_name"],
                    input_cost_per_1k=p["input_cost_per_1k"],
                    output_cost_per_1k=p["output_cost_per_1k"],
                    is_active=True,
                    created_at=datetime.utcnow()
                )
                db.add(record)
                created = True
        if created:
            await db.commit()
        res = await db.execute(select(ModelProviderRecord).order_by(ModelProviderRecord.provider_name))
        return list(res.scalars().all())

    @staticmethod
    async def list_providers(db: AsyncSession, is_active: Optional[bool] = None) -> List[ModelProviderRecord]:
        q = select(ModelProviderRecord)
        if is_active is not None:
            q = q.where(ModelProviderRecord.is_active == is_active)
        res = await db.execute(q.order_by(ModelProviderRecord.provider_name, ModelProviderRecord.model_name))
        return list(res.scalars().all())

    @staticmethod
    async def calculate_cost(db: AsyncSession, model_name: str, input_tokens: int, output_tokens: int) -> float:
        q = select(ModelProviderRecord).where(
            and_(
                ModelProviderRecord.model_name == model_name,
                ModelProviderRecord.is_active == True
            )
        )
        provider = (await db.execute(q)).scalar_one_or_none()
        if not provider:
            return round((input_tokens / 1000.0) * 0.002 + (output_tokens / 1000.0) * 0.006, 6)
        
        in_cost = (input_tokens / 1000.0) * (provider.input_cost_per_1k or 0.002)
        out_cost = (output_tokens / 1000.0) * (provider.output_cost_per_1k or 0.006)
        return round(in_cost + out_cost, 6)


class CustomerIntegrationManager:
    """Manages encrypted customer credentials isolated by tenant_id."""

    @staticmethod
    def encrypt_secret(plain_text: str) -> str:
        cipher = _get_fernet_cipher()
        return cipher.encrypt(plain_text.encode()).decode()

    @staticmethod
    def decrypt_secret(cipher_text: str) -> str:
        cipher = _get_fernet_cipher()
        return cipher.decrypt(cipher_text.encode()).decode()

    @classmethod
    async def store_credential(
        cls,
        db: AsyncSession,
        tenant_id: str,
        provider: str,
        credential_type: Optional[str] = None,
        secret_value: str = "",
        key_identifier: Optional[str] = None,
        scopes: Optional[List[str]] = None,
        expires_at: Optional[datetime] = None
    ) -> CustomerIntegrationCredential:
        encrypted = cls.encrypt_secret(secret_value)
        q = select(CustomerIntegrationCredential).where(
            and_(
                CustomerIntegrationCredential.tenant_id == tenant_id,
                CustomerIntegrationCredential.platform == provider
            )
        )
        existing = (await db.execute(q)).scalar_one_or_none()

        if existing:
            existing.encrypted_access_token = encrypted
            existing.encrypted_secret = encrypted
            existing.expires_at = expires_at
            existing.updated_at = datetime.utcnow()
            await db.commit()
            await db.refresh(existing)
            return existing

        cred = CustomerIntegrationCredential(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            platform=provider,
            encrypted_access_token=encrypted,
            encrypted_secret=encrypted,
            expires_at=expires_at,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(cred)
        await db.commit()
        await db.refresh(cred)
        return cred

    @classmethod
    async def get_credential(
        cls,
        db: AsyncSession,
        tenant_id: str,
        provider: str,
        credential_type: Optional[str] = None,
        reveal_secret: bool = False
    ) -> Optional[Dict[str, Any]]:
        q = select(CustomerIntegrationCredential).where(
            and_(
                CustomerIntegrationCredential.tenant_id == tenant_id,
                CustomerIntegrationCredential.platform == provider
            )
        )
        record = (await db.execute(q)).scalar_one_or_none()
        if not record:
            return None

        result = {
            "id": record.id,
            "tenant_id": record.tenant_id,
            "provider": record.platform,
            "expires_at": record.expires_at.isoformat() if record.expires_at else None,
            "created_at": record.created_at.isoformat() if record.created_at else None
        }
        if reveal_secret:
            result["secret"] = cls.decrypt_secret(record.encrypted_access_token)
        return result

    @classmethod
    async def list_credentials(cls, db: AsyncSession, tenant_id: str) -> List[Dict[str, Any]]:
        q = select(CustomerIntegrationCredential).where(
            CustomerIntegrationCredential.tenant_id == tenant_id
        )
        records = (await db.execute(q)).scalars().all()
        return [
            {
                "id": r.id,
                "tenant_id": r.tenant_id,
                "provider": r.platform,
                "created_at": r.created_at.isoformat() if r.created_at else None
            }
            for r in records
        ]

    @classmethod
    async def delete_credential(cls, db: AsyncSession, tenant_id: str, credential_id: str) -> bool:
        q = select(CustomerIntegrationCredential).where(
            and_(
                CustomerIntegrationCredential.id == credential_id,
                CustomerIntegrationCredential.tenant_id == tenant_id
            )
        )
        record = (await db.execute(q)).scalar_one_or_none()
        if not record:
            return False
        await db.delete(record)
        await db.commit()
        return True
