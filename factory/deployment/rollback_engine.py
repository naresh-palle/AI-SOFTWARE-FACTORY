"""
Automated Rollback Engine.
Restores the previous known stable release automatically upon post-deployment smoke test failures
or manually upon operator request, preserving auditability and separate database safety.
"""

from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy import select, and_, desc

from factory.core.database import get_db_session
from factory.core.logger import logger
from factory.models.schema import DeploymentRelease, RollbackRecord


class RollbackEngine:
    """Manages safe application rollback without compromising database integrity."""

    async def execute_rollback(
        self,
        project_id: str,
        current_release_id: str,
        reason: str,
        trigger_type: str = "automated_health_failure",
    ) -> Dict[str, Any]:
        """Roll back application version to the previous stable release."""
        async with get_db_session() as session:
            # 1. Fetch current release
            curr_q = select(DeploymentRelease).where(DeploymentRelease.id == current_release_id)
            curr_release = (await session.execute(curr_q)).scalar_one_or_none()
            if not curr_release:
                raise ValueError(f"Current release not found: {current_release_id}")

            # 2. Find target stable release (prior active release)
            target_q = (
                select(DeploymentRelease)
                .where(
                    and_(
                        DeploymentRelease.project_id == project_id,
                        DeploymentRelease.environment == curr_release.environment,
                        DeploymentRelease.id != current_release_id,
                        DeploymentRelease.status.in_(["active", "prepared"]),
                    )
                )
                .order_by(desc(DeploymentRelease.created_at))
                .limit(1)
            )
            target_release = (await session.execute(target_q)).scalar_one_or_none()

            if not target_release:
                logger.error(f"RollbackEngine: No previous stable release found for project {project_id}")
                return {
                    "success": False,
                    "reason": "No previous stable release candidate available for rollback.",
                }

            # 3. Mark current release rolled_back
            curr_release.status = "rolled_back"
            curr_release.is_current = False

            # 4. Activate target release
            target_release.status = "active"
            target_release.is_current = True
            target_release.deployed_at = datetime.utcnow()

            # 5. Record Rollback Audit Record
            rec = RollbackRecord(
                project_id=project_id,
                from_release_id=current_release_id,
                to_release_id=target_release.id,
                reason=reason,
                trigger_type=trigger_type,
                status="completed",
                created_at=datetime.utcnow(),
            )
            session.add(rec)
            await session.commit()

        logger.warning(
            f"RollbackEngine: Successfully rolled back project {project_id} from {curr_release.version} to {target_release.version} ({reason})"
        )
        return {
            "success": True,
            "rollback_id": rec.id,
            "from_version": curr_release.version,
            "to_version": target_release.version,
            "environment": curr_release.environment,
            "reason": reason,
            "trigger_type": trigger_type,
        }
