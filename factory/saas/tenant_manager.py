"""
Multi-Tenant Context & Isolation Manager.
Provides tenant context propagation, row-level query scoping,
and cross-tenant data leakage prevention across APIs and background jobs.
"""

from datetime import datetime
from typing import Dict, Any, Optional, Union
from pydantic import BaseModel, Field
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from factory.core.logger import logger
from factory.models.schema import Tenant, Organization, User


class TenantContext(BaseModel):
    """Scoped execution context holding active tenant, organization, and authenticated user."""
    tenant_id: str
    organization_id: Optional[str] = None
    user_id: Optional[str] = None
    user_role: str = "viewer"  # owner, admin, billing_admin, developer, viewer
    is_platform_admin: bool = False


class TenantIsolationError(PermissionError):
    """Raised when an operation attempts to breach tenant isolation boundaries."""
    pass


class TenantManager:
    """Manages tenant lifecycle, status, and strict multi-tenant boundary enforcement."""

    async def create_tenant(
        self,
        db: AsyncSession,
        name: str,
        slug: Optional[str] = None,
    ) -> Tenant:
        """Provision a new independent tenant."""
        tenant = Tenant(
            name=name,
            status="active",
            created_at=datetime.utcnow(),
        )
        db.add(tenant)
        await db.commit()
        await db.refresh(tenant)
        logger.info(f"Provisioned new tenant {tenant.id} ({name})")
        return tenant

    async def get_tenant(
        self,
        db: AsyncSession,
        tenant_id: str,
    ) -> Optional[Tenant]:
        """Fetch tenant record by primary key."""
        q = select(Tenant).where(Tenant.id == tenant_id)
        res = await db.execute(q)
        return res.scalar_one_or_none()

    async def set_tenant_status(
        self,
        db: AsyncSession,
        tenant_id: str,
        status: str,  # active, suspended, deleted
    ) -> Tenant:
        """Update tenant operational status."""
        tenant = await self.get_tenant(db, tenant_id)
        if not tenant:
            raise ValueError(f"Tenant {tenant_id} not found")
        tenant.status = status
        tenant.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(tenant)
        logger.warning(f"Tenant {tenant_id} status updated to '{status}'")
        return tenant

    @classmethod
    def validate_tenant_access(
        cls,
        context: Union[TenantContext, str],
        resource_tenant_id: Optional[str],
        resource_name: str = "Resource",
    ) -> bool:
        """
        Enforce strict tenant boundary.
        Rejects cross-tenant access attempts unless context is platform administrator.
        """
        if isinstance(context, str):
            if not resource_tenant_id or context != resource_tenant_id:
                raise TenantIsolationError(f"Access denied: {resource_name} belongs to another tenant.")
            return True

        if context.is_platform_admin:
            return True

        if not resource_tenant_id or context.tenant_id != resource_tenant_id:
            logger.warning(
                f"SECURITY VIOLATION: Cross-tenant access attempt by tenant '{context.tenant_id}' "
                f"on {resource_name} owned by '{resource_tenant_id}'"
            )
            raise TenantIsolationError(
                f"Access denied: {resource_name} belongs to another tenant."
            )
        return True
