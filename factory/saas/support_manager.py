"""
Customer Support & Notification Manager
Handles tenant support tickets, threaded messages, and in-app notifications.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from sqlalchemy import select, and_, desc, update
from sqlalchemy.ext.asyncio import AsyncSession

from factory.models.schema import SupportTicket, SupportMessage, TenantNotification


class SupportManager:
    """Manages customer support ticket lifecycles and messaging."""

    @staticmethod
    async def create_ticket(
        db: AsyncSession,
        tenant_id: str,
        user_id: str,
        subject: str,
        initial_message: str,
        category: str = "general",
        priority: str = "medium"
    ) -> SupportTicket:
        ticket = SupportTicket(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            created_by_user_id=user_id,
            title=subject,
            status="open",
            priority=priority,
            category=category,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(ticket)
        await db.flush()

        msg = SupportMessage(
            id=str(uuid.uuid4()),
            ticket_id=ticket.id,
            sender_user_id=user_id,
            sender_role="customer",
            message_body=initial_message,
            created_at=datetime.utcnow()
        )
        db.add(msg)
        await db.commit()
        await db.refresh(ticket)
        return ticket

    @staticmethod
    async def add_message(
        db: AsyncSession,
        ticket_id: str,
        sender_id: str,
        sender_role: str,
        message: str
    ) -> SupportMessage:
        q = select(SupportTicket).where(SupportTicket.id == ticket_id)
        ticket = (await db.execute(q)).scalar_one_or_none()
        if not ticket:
            raise ValueError(f"Support ticket {ticket_id} not found")

        msg = SupportMessage(
            id=str(uuid.uuid4()),
            ticket_id=ticket.id,
            sender_user_id=sender_id,
            sender_role=sender_role,
            message_body=message,
            created_at=datetime.utcnow()
        )
        db.add(msg)

        if sender_role in ("support", "support_agent"):
            ticket.status = "waiting_on_customer"
        elif sender_role == "customer" and ticket.status in ("resolved", "waiting_on_customer"):
            ticket.status = "in_progress"

        ticket.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(msg)
        return msg

    @staticmethod
    async def update_status(db: AsyncSession, ticket_id: str, status: str) -> SupportTicket:
        q = select(SupportTicket).where(SupportTicket.id == ticket_id)
        ticket = (await db.execute(q)).scalar_one_or_none()
        if not ticket:
            raise ValueError(f"Support ticket {ticket_id} not found")
        ticket.status = status
        ticket.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(ticket)
        return ticket

    @staticmethod
    async def list_tickets(db: AsyncSession, tenant_id: str, status: Optional[str] = None) -> List[SupportTicket]:
        q = select(SupportTicket).where(SupportTicket.tenant_id == tenant_id)
        if status:
            q = q.where(SupportTicket.status == status)
        res = await db.execute(q.order_by(desc(SupportTicket.created_at)))
        return list(res.scalars().all())

    @staticmethod
    async def get_ticket_details(db: AsyncSession, ticket_id: str, tenant_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        q = select(SupportTicket).where(SupportTicket.id == ticket_id)
        if tenant_id:
            q = q.where(SupportTicket.tenant_id == tenant_id)
        ticket = (await db.execute(q)).scalar_one_or_none()
        if not ticket:
            return None

        q_msg = select(SupportMessage).where(SupportMessage.ticket_id == ticket.id).order_by(SupportMessage.created_at)
        messages = (await db.execute(q_msg)).scalars().all()

        return {
            "id": ticket.id,
            "tenant_id": ticket.tenant_id,
            "user_id": ticket.created_by_user_id,
            "subject": ticket.title,
            "status": ticket.status,
            "priority": ticket.priority,
            "category": ticket.category,
            "created_at": ticket.created_at.isoformat() if ticket.created_at else None,
            "messages": [
                {
                    "id": m.id,
                    "sender_id": m.sender_user_id,
                    "sender_role": m.sender_role,
                    "message": m.message_body,
                    "created_at": m.created_at.isoformat() if m.created_at else None
                }
                for m in messages
            ]
        }


class NotificationManager:
    """Manages transactional and informational tenant in-app notifications."""

    @staticmethod
    async def create_notification(
        db: AsyncSession,
        tenant_id: str,
        title: str,
        message: str,
        severity: str = "info",
        action_url: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> TenantNotification:
        notification = TenantNotification(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            user_id=user_id,
            title=title,
            message=message,
            notification_type=severity,
            is_read=False,
            created_at=datetime.utcnow()
        )
        db.add(notification)
        await db.commit()
        await db.refresh(notification)
        return notification

    @staticmethod
    async def list_notifications(
        db: AsyncSession,
        tenant_id: str,
        unread_only: bool = False,
        limit: int = 50
    ) -> List[TenantNotification]:
        q = select(TenantNotification).where(TenantNotification.tenant_id == tenant_id)
        if unread_only:
            q = q.where(TenantNotification.is_read == False)
        res = await db.execute(q.order_by(desc(TenantNotification.created_at)).limit(limit))
        return list(res.scalars().all())

    @staticmethod
    async def mark_as_read(db: AsyncSession, tenant_id: str, notification_id: str) -> bool:
        q = select(TenantNotification).where(
            and_(
                TenantNotification.id == notification_id,
                TenantNotification.tenant_id == tenant_id
            )
        )
        n = (await db.execute(q)).scalar_one_or_none()
        if not n:
            return False
        n.is_read = True
        await db.commit()
        return True

    @staticmethod
    async def mark_all_as_read(db: AsyncSession, tenant_id: str) -> int:
        stmt = (
            update(TenantNotification)
            .where(
                and_(
                    TenantNotification.tenant_id == tenant_id,
                    TenantNotification.is_read == False
                )
            )
            .values(is_read=True)
        )
        res = await db.execute(stmt)
        await db.commit()
        return res.rowcount
