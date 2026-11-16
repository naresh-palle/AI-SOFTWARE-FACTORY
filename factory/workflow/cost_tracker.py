"""
Worker Cost Governance and Budget Tracking.
Computes runtime expenditure (vCPU/GB-RAM Fargate seconds) and enforces project budget caps.
"""

from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy import select, func

from factory.core.config import settings
from factory.core.database import get_db_session
from factory.models.schema import CostRecord, Project


class CloudCostTracker:
    """Tracks and limits cloud execution costs per project."""

    def __init__(
        self,
        cost_per_vcpu_hour: float = settings.WORKER_COST_PER_VCPU_HOUR_USD,
        cost_per_gb_hour: float = settings.WORKER_COST_PER_GB_HOUR_USD,
    ):
        self.vcpu_sec_rate = cost_per_vcpu_hour / 3600.0
        self.gb_sec_rate = cost_per_gb_hour / 3600.0

    def compute_runtime_cost(
        self,
        duration_seconds: float,
        cpu_cores: int = 2,
        memory_mb: int = 4096,
    ) -> float:
        """Calculate USD cost for Fargate container execution time."""
        memory_gb = memory_mb / 1024.0
        cpu_cost = duration_seconds * cpu_cores * self.vcpu_sec_rate
        mem_cost = duration_seconds * memory_gb * self.gb_sec_rate
        return round(cpu_cost + mem_cost, 6)

    async def record_execution_cost(
        self,
        project_id: str,
        duration_seconds: float,
        cpu_cores: int = 2,
        memory_mb: int = 4096,
        stage_name: str = "cloud_worker_execution",
    ) -> Dict[str, Any]:
        """Record runtime cost into CostRecord entity."""
        amount_usd = self.compute_runtime_cost(duration_seconds, cpu_cores, memory_mb)

        async with get_db_session() as session:
            record = CostRecord(
                project_id=project_id,
                category="compute_cloud_worker",
                amount_usd=amount_usd,
                details={
                    "duration_seconds": round(duration_seconds, 2),
                    "cpu_cores": cpu_cores,
                    "memory_mb": memory_mb,
                    "stage": stage_name,
                    "provider": "aws_fargate",
                },
                recorded_at=datetime.utcnow(),
            )
            session.add(record)
            await session.commit()

        return {
            "project_id": project_id,
            "amount_usd": amount_usd,
            "duration_seconds": duration_seconds,
        }

    async def get_project_total_cost(self, project_id: str) -> float:
        """Sum all recorded costs for a project."""
        async with get_db_session() as session:
            query = select(func.sum(CostRecord.amount_usd)).where(
                CostRecord.project_id == project_id
            )
            result = await session.execute(query)
            total = result.scalar() or 0.0
            return float(total)

    async def is_budget_exceeded(
        self,
        project_id: str,
        budget_limit_usd: Optional[float] = None,
    ) -> bool:
        """Check if project expenditure has reached its maximum budget."""
        limit = budget_limit_usd if budget_limit_usd is not None else settings.PROJECT_DEFAULT_BUDGET_USD
        total = await self.get_project_total_cost(project_id)
        return total >= limit
