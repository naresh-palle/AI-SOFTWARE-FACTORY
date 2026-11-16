"""
Controlled Customer Onboarding & Cohort Rollout Engine.
Manages pilot cohorts, verifies the 14-step onboarding journey,
tracks failures, and enforces automated circuit breakers.
"""

import json
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from factory.core.logger import logger
from factory.models.schema import Tenant, Organization, User, Project, SubscriptionRecord


class OnboardingHaltError(Exception):
    """Raised when the onboarding circuit breaker is tripped due to critical failure."""
    pass


class OnboardingCohortManager:
    """Manages limited, controlled customer cohorts with safety circuit breakers."""

    COHORT_CONFIGS = {
        "pilot_cohort_1": {
            "name": "Phase 11 Pilot Enterprise Cohort",
            "max_tenants": 5,
            "allowed_plans": ["starter", "professional", "business"],
            "requires_manual_approval": True,
        },
        "general_availability": {
            "name": "General Commercial SaaS",
            "max_tenants": 1000,
            "allowed_plans": ["free", "starter", "professional", "business", "enterprise"],
            "requires_manual_approval": False,
        }
    }

    def __init__(self):
        self.circuit_breaker_status: str = "HEALTHY"  # HEALTHY | TRIPPED_HALTED
        self.failure_log: List[Dict[str, Any]] = []

    def check_circuit_breaker(self):
        """Halt onboarding if circuit breaker has tripped."""
        if self.circuit_breaker_status == "TRIPPED_HALTED":
            raise OnboardingHaltError(
                "Customer onboarding is temporarily HALTED by the safety circuit breaker. "
                "A critical failure was detected in an active onboarding cohort. "
                "Resolve open incidents before accepting additional tenants."
            )

    def trip_circuit_breaker(self, tenant_id: str, failed_step: str, error_detail: str):
        """Immediately trip circuit breaker upon critical failure."""
        self.circuit_breaker_status = "TRIPPED_HALTED"
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "tenant_id": tenant_id,
            "failed_step": failed_step,
            "error_detail": error_detail,
        }
        self.failure_log.append(entry)
        logger.error(f"CIRCUIT BREAKER TRIPPED by tenant {tenant_id} at step {failed_step}: {error_detail}")

    def reset_circuit_breaker(self, operator_reason: str):
        """Operator override to reset circuit breaker after remediation."""
        self.circuit_breaker_status = "HEALTHY"
        logger.info(f"Circuit breaker manually reset to HEALTHY. Reason: {operator_reason}")

    async def validate_cohort_capacity(
        self,
        db: AsyncSession,
        cohort_id: str = "pilot_cohort_1",
    ) -> Dict[str, Any]:
        """Verify cohort has available quota before permitting onboarding."""
        self.check_circuit_breaker()
        config = self.COHORT_CONFIGS.get(cohort_id, self.COHORT_CONFIGS["pilot_cohort_1"])

        # Count active tenants
        q_count = select(func.count(Tenant.id)).where(Tenant.status == "active")
        active_count = (await db.execute(q_count)).scalar() or 0

        max_limit = config["max_tenants"]
        available_slots = max(0, max_limit - active_count)

        return {
            "cohort_id": cohort_id,
            "cohort_name": config["name"],
            "max_capacity": max_limit,
            "active_tenants": active_count,
            "available_slots": available_slots,
            "can_onboard": available_slots > 0 and self.circuit_breaker_status == "HEALTHY",
            "circuit_breaker": self.circuit_breaker_status,
        }

    async def verify_14_step_onboarding_journey(
        self,
        tenant_id: str,
        user_id: str,
        org_id: str,
        project_id: str,
        subscription_tier: str,
        steps_evidence: Dict[str, bool],
    ) -> Dict[str, Any]:
        """
        Verify the 14 mandatory customer onboarding journey gates:
        1. Registration
        2. Email verification
        3. Organization creation
        4. Subscription selection
        5. Payment
        6. Project creation
        7. Requirement submission
        8. AI analysis
        9. Code generation
        10. Testing
        11. GitHub integration
        12. Deployment preparation
        13. Usage metering
        14. Billing
        """
        self.check_circuit_breaker()

        mandatory_steps = [
            "01_registration",
            "02_email_verification",
            "03_organization_creation",
            "04_subscription_selection",
            "05_payment",
            "06_project_creation",
            "07_requirement_submission",
            "08_ai_analysis",
            "09_code_generation",
            "10_testing",
            "11_github_integration",
            "12_deployment_preparation",
            "13_usage_metering",
            "14_billing_invoice",
        ]

        results = {}
        for step in mandatory_steps:
            passed = steps_evidence.get(step, False)
            results[step] = "PASSED" if passed else "FAILED"
            if not passed:
                self.trip_circuit_breaker(
                    tenant_id=tenant_id,
                    failed_step=step,
                    error_detail=f"Customer onboarding validation failed at gate {step}",
                )
                raise OnboardingHaltError(f"Customer onboarding failed at gate '{step}'. Circuit breaker tripped.")

        return {
            "tenant_id": tenant_id,
            "user_id": user_id,
            "organization_id": org_id,
            "project_id": project_id,
            "subscription_tier": subscription_tier,
            "status": "COMPLETED_VERIFIED",
            "steps_verified_count": len(mandatory_steps),
            "step_results": results,
            "verified_at": datetime.now(timezone.utc).isoformat(),
        }
