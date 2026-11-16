"""
SaaS Platform Module
Multi-tenant isolation, customer auth, org/teams, subscription/billing, usage metering, and provider credentials.
"""

from factory.saas.tenant_manager import TenantManager, TenantContext, TenantIsolationError
from factory.saas.auth_manager import CustomerAuthManager
from factory.saas.org_manager import OrganizationManager
from factory.saas.subscription_manager import SubscriptionManager
from factory.saas.billing_engine import PaymentBillingEngine
from factory.saas.usage_meter import UsageMeteringEngine, QuotaExceededError
from factory.saas.model_provider_manager import ModelCatalogManager, CustomerIntegrationManager
from factory.saas.support_manager import SupportManager, NotificationManager
from factory.saas.admin_console import SaaSAdminConsole

__all__ = [
    "TenantManager",
    "TenantContext",
    "TenantIsolationError",
    "CustomerAuthManager",
    "OrganizationManager",
    "SubscriptionManager",
    "PaymentBillingEngine",
    "UsageMeteringEngine",
    "QuotaExceededError",
    "ModelCatalogManager",
    "CustomerIntegrationManager",
    "SupportManager",
    "NotificationManager",
    "SaaSAdminConsole",
]
