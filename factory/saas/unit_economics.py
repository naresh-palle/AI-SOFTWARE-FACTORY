"""
Unit Economics, FinOps Cost Modeling & Spending Cap Engine.
Calculates COGS, gross margins, infrastructure amortization, and spending caps per tier.
"""

from typing import Dict, Any, List


class UnitEconomicsEngine:
    """Calculates defensible commercial unit economics and enforces customer spending caps."""

    # 1. Base AWS & Infrastructure Rates
    FARGATE_VCPU_HOUR = 0.04048
    FARGATE_GB_RAM_HOUR = 0.004445
    S3_GB_MONTH = 0.023
    DATA_TRANSFER_OUT_GB = 0.09
    RDS_HOURLY_AMORTIZED = 0.068  # db.t4g.medium pooled across tenants
    REDIS_HOURLY_AMORTIZED = 0.024  # cache.t4g.small pooled

    # 2. Blended AI Token Pricing ($ per 1,000 tokens)
    BLENDED_AI_TOKEN_COST_PER_1K = 0.004  # 70% flash/mini, 30% pro/sonnet

    # 3. Plan Specifications & Allowances
    PLAN_CONFIGS = {
        "free": {
            "name": "Community Free",
            "monthly_price_usd": 0.0,
            "monthly_token_allowance": 100_000,
            "worker_minutes_allowance": 60,
            "s3_storage_gb": 1.0,
            "support_tier": "community",
            "payment_gateway_rate": 0.0,
            "fixed_payment_fee": 0.0,
            "spending_cap_usd": 1.0,  # Strict cap on free tier
            "overage_token_price_per_1k": 0.0,  # Must upgrade
        },
        "starter": {
            "name": "Developer Starter",
            "monthly_price_usd": 49.0,
            "monthly_token_allowance": 1_000_000,
            "worker_minutes_allowance": 250,
            "s3_storage_gb": 10.0,
            "support_tier": "email_48h",
            "payment_gateway_rate": 0.029,  # Stripe 2.9%
            "fixed_payment_fee": 0.30,
            "spending_cap_usd": 25.0,
            "overage_token_price_per_1k": 0.008,
        },
        "professional": {
            "name": "Engineering Professional",
            "monthly_price_usd": 199.0,
            "monthly_token_allowance": 5_000_000,
            "worker_minutes_allowance": 1_000,
            "s3_storage_gb": 50.0,
            "support_tier": "priority_24h",
            "payment_gateway_rate": 0.029,
            "fixed_payment_fee": 0.30,
            "spending_cap_usd": 90.0,
            "overage_token_price_per_1k": 0.007,
        },
        "business": {
            "name": "Autonomous Business",
            "monthly_price_usd": 499.0,
            "monthly_token_allowance": 25_000_000,
            "worker_minutes_allowance": 5_000,
            "s3_storage_gb": 200.0,
            "support_tier": "dedicated_12h",
            "payment_gateway_rate": 0.025,
            "fixed_payment_fee": 0.30,
            "spending_cap_usd": 220.0,
            "overage_token_price_per_1k": 0.006,
        },
        "enterprise": {
            "name": "Enterprise Autonomous Factory",
            "monthly_price_usd": 1999.0,
            "monthly_token_allowance": 100_000_000,
            "worker_minutes_allowance": 50_000,
            "s3_storage_gb": 1000.0,
            "support_tier": "dedicated_sla_1h",
            "payment_gateway_rate": 0.022,
            "fixed_payment_fee": 0.30,
            "spending_cap_usd": 900.0,
            "overage_token_price_per_1k": 0.005,
        },
    }

    @classmethod
    def calculate_plan_unit_economics(cls, plan_tier: str) -> Dict[str, Any]:
        """Itemize COGS, gross margin, and cost breakdowns for a tier."""
        plan = cls.PLAN_CONFIGS.get(plan_tier.lower())
        if not plan:
            raise ValueError(f"Unknown tier '{plan_tier}'")

        revenue = plan["monthly_price_usd"]

        # 1. Estimated AI Token Expense
        tokens_1k = plan["monthly_token_allowance"] / 1000.0
        ai_expense = round(tokens_1k * cls.BLENDED_AI_TOKEN_COST_PER_1K, 2)

        # 2. Worker Fargate Compute Expense (1 vCPU, 2GB RAM per worker task)
        worker_hours = plan["worker_minutes_allowance"] / 60.0
        fargate_rate_per_hour = (1.0 * cls.FARGATE_VCPU_HOUR) + (2.0 * cls.FARGATE_GB_RAM_HOUR)
        compute_expense = round(worker_hours * fargate_rate_per_hour, 2)

        # 3. Storage & Infrastructure Amortization
        storage_expense = round(plan["s3_storage_gb"] * cls.S3_GB_MONTH, 2)
        infra_overhead = round(0.50 if plan_tier != "free" else 0.10, 2)  # Pooled DB/Redis/CloudWatch per active tenant

        # 4. Payment Gateway Cost
        payment_fee = round((revenue * plan["payment_gateway_rate"]) + (plan["fixed_payment_fee"] if revenue > 0 else 0.0), 2)

        # 5. Support Operations Cost
        support_cost_map = {
            "community": 0.10,
            "email_48h": 2.50,
            "priority_24h": 8.00,
            "dedicated_12h": 25.00,
            "dedicated_sla_1h": 120.00
        }
        support_expense = support_cost_map.get(plan["support_tier"], 2.00)

        # Total COGS
        total_cogs = round(ai_expense + compute_expense + storage_expense + infra_overhead + payment_fee + support_expense, 2)
        gross_profit = round(revenue - total_cogs, 2)
        gross_margin_pct = round((gross_profit / revenue) * 100.0, 1) if revenue > 0 else 0.0

        return {
            "plan_tier": plan_tier,
            "plan_name": plan["name"],
            "monthly_revenue_usd": revenue,
            "cogs_breakdown": {
                "ai_token_expenditure_usd": ai_expense,
                "cloud_worker_fargate_usd": compute_expense,
                "s3_storage_and_bandwidth_usd": storage_expense,
                "infrastructure_pooled_usd": infra_overhead,
                "payment_gateway_fees_usd": payment_fee,
                "support_operations_usd": support_expense,
                "total_cogs_usd": total_cogs,
            },
            "financial_metrics": {
                "gross_profit_usd": gross_profit,
                "gross_margin_percentage": gross_margin_pct,
                "spending_cap_ceiling_usd": plan["spending_cap_usd"],
                "overage_token_price_per_1k": plan["overage_token_price_per_1k"],
            }
        }

    @classmethod
    def evaluate_spending_cap(cls, plan_tier: str, current_incurred_cost_usd: float) -> Dict[str, Any]:
        """Enforces hard ceiling on customer resource expenditure to prevent runaway loss."""
        plan = cls.PLAN_CONFIGS.get(plan_tier.lower())
        if not plan:
            raise ValueError(f"Unknown tier '{plan_tier}'")

        cap = plan["spending_cap_usd"]
        is_breached = current_incurred_cost_usd >= cap
        pct = round((current_incurred_cost_usd / cap) * 100.0, 1) if cap > 0 else 100.0

        return {
            "plan_tier": plan_tier,
            "spending_cap_usd": cap,
            "current_cost_usd": current_incurred_cost_usd,
            "percentage_consumed": pct,
            "is_breached": is_breached,
            "action_required": "HALT_EXECUTION_UPGRADE_REQUIRED" if is_breached else "PROCEED"
        }
