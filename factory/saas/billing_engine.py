"""
Payment Gateway Abstraction & Billing Engine.
Supports Stripe (International) and Razorpay (India/UPI) payment processors,
cryptographic webhook signature verification, idempotency keys, and automated invoicing.
"""

import hmac
import hashlib
import json
import secrets
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from sqlalchemy import select, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from factory.core.logger import logger
from factory.models.schema import (
    PaymentTransaction,
    InvoiceRecord,
    PaymentWebhookEvent,
    SubscriptionRecord,
    SubscriptionPlan,
    Organization,
)
from factory.saas.subscription_manager import SubscriptionManager


class PaymentBillingEngine:
    """Manages payment gateway abstractions, webhooks, transactions, and invoice issuance."""

    STRIPE_WEBHOOK_SECRET = "whsec_test_stripe_secret_key_mock_32b"
    RAZORPAY_WEBHOOK_SECRET = "whsec_test_razorpay_secret_key_mock_32b"

    def __init__(self):
        self.subscription_manager = SubscriptionManager()

    @classmethod
    def verify_webhook_signature(
        cls,
        payload_bytes: bytes,
        signature: str,
        provider: str = "stripe",
    ) -> bool:
        """Verify HMAC-SHA256 signature on incoming payment gateway webhook."""
        secret = cls.STRIPE_WEBHOOK_SECRET if provider == "stripe" else cls.RAZORPAY_WEBHOOK_SECRET
        computed_sig = hmac.new(
            secret.encode("utf-8"),
            payload_bytes,
            hashlib.sha256,
        ).hexdigest()

        # Handle provider prefix if present
        cleaned_sig = signature.replace("sha256=", "").replace("t=", "").split(",")[-1]
        return hmac.compare_digest(computed_sig, cleaned_sig)

    async def process_payment(
        self,
        db: AsyncSession,
        tenant_id: str,
        amount: float,
        organization_id: Optional[str] = None,
        currency: str = "USD",
        provider: str = "stripe",
        gateway: Optional[str] = None,
        idempotency_key: Optional[str] = None,
        subscription_id: Optional[str] = None,
        description: Optional[str] = None,
    ) -> PaymentTransaction:
        """Process sandbox payment charge with strict idempotency protection."""
        i_key = idempotency_key or f"idem_{secrets.token_hex(16)}"
        active_provider = (gateway or provider or "stripe").lower()

        if not organization_id:
            q_org = select(Organization).where(Organization.tenant_id == tenant_id)
            org = (await db.execute(q_org)).scalar_one_or_none()
            if not org:
                org = Organization(
                    tenant_id=tenant_id,
                    name=f"Org-{tenant_id[:8]}",
                    slug=f"org-{tenant_id[:8]}",
                    billing_email=f"billing@{tenant_id[:8]}.local",
                    created_at=datetime.utcnow(),
                )
                db.add(org)
                await db.flush()
            organization_id = org.id

        # Check existing transaction by idempotency key
        q_idem = select(PaymentTransaction).where(PaymentTransaction.idempotency_key == i_key)
        existing = (await db.execute(q_idem)).scalar_one_or_none()
        if existing:
            logger.info(f"Idempotent payment re-play: Returning existing transaction {existing.id}")
            return existing

        provider_payment_id = f"pay_{active_provider}_{secrets.token_hex(12)}"

        tx = PaymentTransaction(
            tenant_id=tenant_id,
            organization_id=organization_id,
            subscription_id=subscription_id,
            amount=amount,
            currency=currency.upper(),
            provider=active_provider,
            provider_payment_id=provider_payment_id,
            idempotency_key=i_key,
            status="succeeded",
            created_at=datetime.utcnow(),
        )
        db.add(tx)
        await db.flush()

        # Generate Invoice
        invoice_number = f"INV-{datetime.utcnow().strftime('%Y%m')}-{secrets.token_hex(4).upper()}"
        invoice = InvoiceRecord(
            tenant_id=tenant_id,
            organization_id=organization_id,
            invoice_number=invoice_number,
            amount_due=amount,
            amount_paid=amount,
            currency=currency.upper(),
            status="paid",
            due_date=datetime.utcnow(),
            paid_at=datetime.utcnow(),
            invoice_pdf_url=f"/api/v1/saas/invoices/{invoice_number}.pdf",
            created_at=datetime.utcnow(),
        )
        db.add(invoice)
        await db.commit()
        await db.refresh(tx)

        logger.info(f"Processed payment {tx.id} (${amount} {currency}) via {active_provider}. Issued {invoice_number}")
        return tx

    async def handle_webhook_event(
        self,
        db: AsyncSession,
        provider: Optional[str] = None,
        event_id: Optional[str] = None,
        event_type: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
        signature: Optional[str] = None,
        gateway: Optional[str] = None,
        raw_payload: Optional[bytes] = None,
        signature_header: Optional[str] = None,
        payload_data: Optional[Dict[str, Any]] = None,
        webhook_secret: Optional[str] = None,
    ) -> Any:
        """
        Process gateway webhook events asynchronously:
        - invoice.payment_succeeded
        - invoice.payment_failed
        - customer.subscription.deleted
        """
        active_provider = (gateway or provider or "stripe").lower()
        active_payload = payload_data or payload or {}
        active_event_id = event_id or active_payload.get("id") or f"evt_{secrets.token_hex(8)}"
        active_event_type = event_type or active_payload.get("type") or "payment.succeeded"

        # Verify signature if raw payload and header provided
        if raw_payload and signature_header:
            secret = webhook_secret or (self.STRIPE_WEBHOOK_SECRET if active_provider == "stripe" else self.RAZORPAY_WEBHOOK_SECRET)
            computed_sig = hmac.new(secret.encode("utf-8"), raw_payload, hashlib.sha256).hexdigest()
            cleaned_sig = signature_header.replace("sha256=", "").replace("t=", "").split(",")[-1]
            if not hmac.compare_digest(computed_sig, cleaned_sig):
                logger.warning(f"Invalid webhook signature for {active_provider}")
                raise ValueError("Invalid webhook signature")

        # Deduplicate webhook event
        q = select(PaymentWebhookEvent).where(PaymentWebhookEvent.event_id == active_event_id)
        existing = (await db.execute(q)).scalar_one_or_none()
        if existing:
            return existing

        event_rec = PaymentWebhookEvent(
            provider=active_provider,
            event_id=active_event_id,
            event_type=active_event_type,
            payload_json=active_payload,
            processed=True,
            created_at=datetime.utcnow(),
        )
        db.add(event_rec)

        if active_event_type in ["invoice.payment_succeeded", "payment.captured", "charge.succeeded"]:
            logger.info(f"Payment webhook confirmed: {active_event_type} for event {active_event_id}")
        elif active_event_type in ["customer.subscription.deleted", "subscription.cancelled"]:
            logger.warning(f"Subscription cancellation webhook received: {active_event_id}")

        await db.commit()
        await db.refresh(event_rec)
        return event_rec

    async def list_invoices(
        self,
        db: AsyncSession,
        tenant_id: str,
    ) -> List[InvoiceRecord]:
        """List billing invoices for tenant."""
        q = select(InvoiceRecord).where(InvoiceRecord.tenant_id == tenant_id).order_by(desc(InvoiceRecord.created_at))
        res = await db.execute(q)
        return list(res.scalars().all())
