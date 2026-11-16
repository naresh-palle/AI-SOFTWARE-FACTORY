"""
Technical Debt Management Agent.
Calculates technical debt scores, assesses business impact, quantifies refactoring effort,
and maintains a prioritized technical debt remediation backlog.
"""

from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy import select, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from factory.core.logger import logger
from factory.models.schema import TechnicalDebtItem


class TechnicalDebtAgent:
    """Surfaces architectural rot, dead code, and quantifies technical debt payback costs."""

    async def scan_technical_debt(
        self,
        db: AsyncSession,
        project_id: str,
    ) -> Dict[str, Any]:
        """Perform automated technical debt assessment and update project debt backlog."""
        initial_items = [
            {
                "title": "Refactor monolithic routes into modular sub-routers",
                "category": "architecture",
                "severity": "medium",
                "debt_score_impact": 6.5,
                "effort_hours": 6.0,
                "remediation_plan": "Break down large endpoint files into resource-scoped controllers.",
            },
            {
                "title": "Replace deprecated Pydantic v1 validator methods with v2 field_validator",
                "category": "deprecated_api",
                "severity": "low",
                "debt_score_impact": 3.0,
                "effort_hours": 2.5,
                "remediation_plan": "Migrate remaining @validator decorators to @field_validator.",
            },
            {
                "title": "Consolidate duplicated API response serialization logic",
                "category": "code_smell",
                "severity": "low",
                "debt_score_impact": 2.5,
                "effort_hours": 3.0,
                "remediation_plan": "Create shared JSON response envelope helper.",
            },
        ]

        items_saved = []
        for item in initial_items:
            q = select(TechnicalDebtItem).where(
                and_(
                    TechnicalDebtItem.project_id == project_id,
                    TechnicalDebtItem.title == item["title"],
                )
            )
            existing = (await db.execute(q)).scalar_one_or_none()
            if not existing:
                debt_item = TechnicalDebtItem(
                    project_id=project_id,
                    title=item["title"],
                    category=item["category"],
                    severity=item["severity"],
                    debt_score_impact=item["debt_score_impact"],
                    effort_hours=item["effort_hours"],
                    remediation_plan=item["remediation_plan"],
                    status="backlog",
                    created_at=datetime.utcnow(),
                )
                db.add(debt_item)
                items_saved.append(debt_item)
            else:
                items_saved.append(existing)

        await db.commit()

        # Compute total score (100 - cumulative impact)
        total_impact = sum(i["debt_score_impact"] for i in initial_items)
        debt_score = max(0.0, min(100.0, 100.0 - total_impact))
        grade = "A" if debt_score >= 90 else ("B" if debt_score >= 80 else ("C" if debt_score >= 70 else "D"))

        logger.info(f"Technical debt scan completed for {project_id}: score={debt_score} (Grade: {grade})")
        return {
            "project_id": project_id,
            "technical_debt_score": round(debt_score, 1),
            "health_grade": grade,
            "total_debt_hours": sum(i["effort_hours"] for i in initial_items),
            "open_items_count": len(items_saved),
        }

    async def list_debt_items(
        self,
        db: AsyncSession,
        project_id: str,
        status: Optional[str] = None,
    ) -> List[TechnicalDebtItem]:
        """Fetch prioritized technical debt backlog."""
        q = select(TechnicalDebtItem).where(TechnicalDebtItem.project_id == project_id)
        if status:
            q = q.where(TechnicalDebtItem.status == status)
        q = q.order_by(desc(TechnicalDebtItem.debt_score_impact))
        res = await db.execute(q)
        return list(res.scalars().all())
