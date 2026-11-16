"""
Organization & Role-Based Access Control (RBAC) Manager.
Enforces granular permission checks across 8 organizational roles
and coordinates team invites, memberships, and role assignments.
"""

import secrets
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from factory.core.logger import logger
from factory.models.schema import Organization, OrganizationMember, OrganizationInvitation, User


class PermissionDeniedError(PermissionError):
    """Raised when an action is prohibited by RBAC policy."""
    pass


class OrganizationManager:
    """Manages team membership, organization lifecycle, and RBAC matrix enforcement."""

    ROLE_PERMISSIONS: Dict[str, List[str]] = {
        "owner": [
            "create_project", "modify_project", "delete_project",
            "execute_workflow", "manage_members", "manage_billing",
            "deploy_application", "approve_releases", "view_logs",
            "manage_integrations", "manage_quotas"
        ],
        "admin": [
            "create_project", "modify_project",
            "execute_workflow", "manage_members",
            "deploy_application", "approve_releases", "view_logs",
            "manage_integrations"
        ],
        "billing_admin": [
            "manage_billing", "view_invoices", "view_logs"
        ],
        "project_manager": [
            "create_project", "modify_project", "execute_workflow",
            "view_logs", "approve_releases"
        ],
        "developer": [
            "create_project", "modify_project", "execute_workflow", "view_logs"
        ],
        "qa_engineer": [
            "execute_workflow", "view_logs"
        ],
        "viewer": [
            "view_logs"
        ],
        "collaborator": [
            "view_logs"
        ],
    }

    @classmethod
    def has_permission(cls, role: str, action: str) -> bool:
        """Check if an organization role is permitted to perform an action."""
        perms = cls.ROLE_PERMISSIONS.get(role.lower(), [])
        return action in perms

    @classmethod
    def assert_permission(cls, role: str, action: str):
        """Raise PermissionError if role lacks required permission."""
        if not cls.has_permission(role, action):
            logger.warning(f"RBAC DENIED: Role '{role}' lacks permission '{action}'")
            raise PermissionDeniedError(f"Role '{role}' is not authorized to perform '{action}'.")

    async def create_organization(
        self,
        db: AsyncSession,
        tenant_id: str,
        name: str,
        billing_email: str,
        owner_user_id: Optional[str] = None,
    ) -> Organization:
        """Create a new organization within a tenant."""
        slug = name.lower().replace(" ", "-") + f"-{secrets.token_hex(3)}"
        org = Organization(
            tenant_id=tenant_id,
            name=name,
            slug=slug,
            billing_email=billing_email,
            created_at=datetime.utcnow(),
        )
        db.add(org)
        await db.flush()

        if owner_user_id:
            member = OrganizationMember(
                organization_id=org.id,
                user_id=owner_user_id,
                role="owner",
                is_active=True,
                joined_at=datetime.utcnow(),
            )
            db.add(member)

        await db.commit()
        await db.refresh(org)
        logger.info(f"Created organization {org.id} ({name}) in tenant {tenant_id}")
        return org

    async def invite_member(
        self,
        db: AsyncSession,
        organization_id: Optional[str] = None,
        email: str = "",
        role: str = "developer",
        invited_by_id: Optional[str] = None,
        org_id: Optional[str] = None,
        invited_by: Optional[str] = None,
    ) -> OrganizationInvitation:
        """Issue an email team invitation token valid for 7 days."""
        target_org_id = org_id or organization_id
        target_invited_by = invited_by or invited_by_id
        if not target_org_id:
            raise ValueError("organization_id is required")

        if role not in self.ROLE_PERMISSIONS:
            role = "developer"

        token = secrets.token_urlsafe(32)
        invitation = OrganizationInvitation(
            organization_id=target_org_id,
            email=email.lower().strip(),
            role=role,
            token=token,
            status="pending",
            invited_by_id=target_invited_by,
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(days=7),
        )
        db.add(invitation)
        await db.commit()
        await db.refresh(invitation)
        logger.info(f"Created invitation {invitation.id} for {email} ({role}) in org {organization_id}")
        return invitation

    async def accept_invitation(
        self,
        db: AsyncSession,
        token: str,
        user_id: str,
    ) -> OrganizationMember:
        """Accept pending invitation and bind user as active organization member."""
        q = select(OrganizationInvitation).where(
            and_(
                OrganizationInvitation.token == token,
                OrganizationInvitation.status == "pending",
                OrganizationInvitation.expires_at > datetime.utcnow(),
            )
        )
        res = await db.execute(q)
        inv = res.scalar_one_or_none()
        if not inv:
            raise ValueError("Invalid or expired invitation token.")

        inv.status = "accepted"

        member = OrganizationMember(
            organization_id=inv.organization_id,
            user_id=user_id,
            role=inv.role,
            is_active=True,
            joined_at=datetime.utcnow(),
        )
        db.add(member)
        await db.commit()
        await db.refresh(member)
        logger.info(f"User {user_id} joined org {inv.organization_id} via invitation {inv.id}")
        return member

    async def list_members(
        self,
        db: AsyncSession,
        organization_id: str,
    ) -> List[Dict[str, Any]]:
        """List active members and roles for an organization."""
        q = select(OrganizationMember, User).join(User, OrganizationMember.user_id == User.id).where(
            OrganizationMember.organization_id == organization_id
        )
        res = await db.execute(q)
        rows = res.all()
        return [
            {
                "member_id": m.id,
                "user_id": u.id,
                "email": u.email,
                "full_name": u.full_name,
                "role": m.role,
                "joined_at": m.joined_at.isoformat() if m.joined_at else None,
            }
            for m, u in rows
        ]
