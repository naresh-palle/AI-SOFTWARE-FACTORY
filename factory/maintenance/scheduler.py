"""
Autonomous Maintenance Scheduler.
Orchestrates scheduled and event-triggered post-deployment maintenance tasks
under strict project-specific policies and safety levels.
"""

from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy import select, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from factory.core.logger import logger
from factory.models.schema import MaintenancePolicy, MaintenanceTask, ApprovalRecord


class MaintenanceScheduler:
    """Manages periodic, event-driven, and on-demand maintenance workflows."""

    VALID_SCHEDULES = ["daily", "weekly", "monthly", "on_demand"]
    VALID_TYPES = [
        "code_quality",
        "dependency_update",
        "security_remediation",
        "bug_fix",
        "database_maintenance",
        "performance_optimization",
        "technical_debt",
        "documentation",
        "continuous_improvement",
    ]
    VALID_TRIGGERS = [
        "scheduled",
        "on_demand",
        "security_event",
        "incident_event",
        "dependency_event",
        "performance_event",
    ]

    AGENT_ASSIGNMENTS = {
        "code_quality": [97],  # Application Maintenance Agent
        "dependency_update": [96],  # Dependency Update Agent
        "security_remediation": [62, 87],  # Vulnerability Scanning & Security Testing
        "bug_fix": [89],  # Bug Fixing Agent
        "database_maintenance": [26],  # PostgreSQL Agent
        "performance_optimization": [14, 86],  # Frontend Performance & Performance Testing
        "technical_debt": [97],  # Application Maintenance Agent
        "documentation": [7, 97],  # Project Planning & Maintenance
        "continuous_improvement": [7, 89, 96, 97],
    }

    async def configure_policy(
        self,
        db: AsyncSession,
        project_id: str,
        schedule: str = "daily",
        is_enabled: bool = True,
        auto_remediate_level1: bool = True,
        require_approval_level2: bool = True,
        maintenance_window: str = "02:00-04:00 UTC",
    ) -> MaintenancePolicy:
        """Configure or update maintenance execution policy for a project."""
        if schedule not in self.VALID_SCHEDULES:
            schedule = "daily"

        q = select(MaintenancePolicy).where(MaintenancePolicy.project_id == project_id)
        res = await db.execute(q)
        policy = res.scalar_one_or_none()

        if policy:
            policy.schedule = schedule
            policy.is_enabled = is_enabled
            policy.auto_remediate_level1 = auto_remediate_level1
            policy.require_approval_level2 = require_approval_level2
            policy.maintenance_window = maintenance_window
            policy.updated_at = datetime.utcnow()
        else:
            policy = MaintenancePolicy(
                project_id=project_id,
                schedule=schedule,
                is_enabled=is_enabled,
                auto_remediate_level1=auto_remediate_level1,
                require_approval_level2=require_approval_level2,
                maintenance_window=maintenance_window,
                created_at=datetime.utcnow(),
            )
            db.add(policy)

        await db.commit()
        await db.refresh(policy)
        logger.info(f"Configured maintenance policy for project {project_id} (schedule={schedule})")
        return policy

    async def get_policy(
        self,
        db: AsyncSession,
        project_id: str,
    ) -> MaintenancePolicy:
        """Fetch project maintenance policy or default configuration."""
        q = select(MaintenancePolicy).where(MaintenancePolicy.project_id == project_id)
        res = await db.execute(q)
        policy = res.scalar_one_or_none()
        if not policy:
            return await self.configure_policy(db, project_id)
        return policy

    async def schedule_task(
        self,
        db: AsyncSession,
        project_id: str,
        maintenance_type: str,
        trigger_type: str = "scheduled",
        priority: str = "medium",
        assigned_agents: Optional[List[int]] = None,
        git_branch: Optional[str] = None,
    ) -> MaintenanceTask:
        """Create and queue a new maintenance task."""
        if maintenance_type not in self.VALID_TYPES:
            raise ValueError(f"Invalid maintenance type '{maintenance_type}'. Must be one of {self.VALID_TYPES}")

        agents = assigned_agents or self.AGENT_ASSIGNMENTS.get(maintenance_type, [97])

        task = MaintenanceTask(
            project_id=project_id,
            maintenance_type=maintenance_type,
            trigger_type=trigger_type,
            priority=priority,
            assigned_agents=agents,
            status="scheduled",
            git_branch=git_branch or f"maintenance/{maintenance_type}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            results={},
            logs=f"Maintenance task queued [{trigger_type}] with priority {priority}. Assigned agents: {agents}",
            created_at=datetime.utcnow(),
        )
        db.add(task)
        await db.commit()
        await db.refresh(task)
        logger.info(f"Queued maintenance task {task.id} ({maintenance_type}) for project {project_id}")
        return task

    async def list_tasks(
        self,
        db: AsyncSession,
        project_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
    ) -> List[MaintenanceTask]:
        """Fetch historical and active maintenance tasks."""
        q = select(MaintenanceTask)
        if project_id:
            q = q.where(MaintenanceTask.project_id == project_id)
        if status:
            q = q.where(MaintenanceTask.status == status)
        q = q.order_by(desc(MaintenanceTask.created_at)).limit(limit)
        res = await db.execute(q)
        return list(res.scalars().all())

    async def get_task(
        self,
        db: AsyncSession,
        task_id: str,
    ) -> Optional[MaintenanceTask]:
        """Get single maintenance task with execution log and results."""
        q = select(MaintenanceTask).where(MaintenanceTask.id == task_id)
        res = await db.execute(q)
        return res.scalar_one_or_none()
