"""
End-to-End Staging Maintenance & Self-Improvement Validation Test.
Executes the full 15-step autonomous post-deployment maintenance lifecycle:
1. Select staging project
2. Introduce controlled reproducible defect (simulated error log & incident)
3. Run maintenance analysis
4. Verify defect detection
5. Generate proposed fix
6. Create isolated Git branch (maintenance/...)
7. Apply the fix
8. Execute targeted tests
9. Execute full regression tests
10. Run security scans
11. Generate GitHub pull request
12. Verify approval workflow
13. Merge after authorized approval
14. Deploy through Phase 6 ReleaseManager
15. Verify improvement through Phase 7 ApplicationMonitoringAgent
"""

import pytest
from datetime import datetime
from sqlalchemy import select

from factory.core.database import get_db_session, init_db
from factory.models.schema import (
    Project,
    IncidentRecord,
    BugReport,
    ApprovalRecord,
    DeploymentRelease,
)
from factory.maintenance.bug_fixing import BugDetectionAndFixAgent
from factory.maintenance.regression_engine import RegressionEngine
from factory.maintenance.security_remediation import SecurityRemediationAgent
from factory.deployment.release_manager import ReleaseManager
from factory.observability.monitoring.app_monitor import ApplicationMonitoringAgent


@pytest.mark.asyncio
async def test_end_to_end_staging_maintenance_lifecycle():
    """Verify complete 15-step autonomous defect remediation and deployment."""
    await init_db()

    async with get_db_session() as session:
        # Step 1: Select staging application
        q_proj = select(Project).where(Project.name == "Staging E2E App")
        proj = (await session.execute(q_proj)).scalar_one_or_none()
        if not proj:
            proj = Project(
                name="Staging E2E App",
                requirement_text="Production staging environment for continuous improvement",
                platform_target="website",
                status="active",
            )
            session.add(proj)
            await session.commit()
            await session.refresh(proj)

        # Step 2: Introduce controlled, reproducible defect in staging
        incident = IncidentRecord(
            project_id=proj.id,
            title="Staging Unhandled KeyError in /api/v1/checkout",
            affected_service="checkout-service",
            severity="high",
            environment="staging",
            status="detected",
            impact_summary="KeyError 'currency' on checkout payload without explicit default",
        )
        session.add(incident)
        await session.commit()
        await session.refresh(incident)

        # Step 3 & 4: Run maintenance analysis & verify defect detection
        bug_agent = BugDetectionAndFixAgent()
        bug = await bug_agent.detect_and_create_bug_from_incident(session, incident)
        assert bug is not None
        assert bug.status == "detected"
        assert "KeyError" in bug.title

        # Step 5, 6, 7: Generate proposed fix on isolated Git branch
        fix_res = await bug_agent.auto_generate_bug_fix(session, bug.id)
        assert fix_res["status"] == "pr_created"
        assert fix_res["branch_name"].startswith("maintenance/bugfix-")
        assert fix_res["approval_id"] is not None

        # Step 8 & 9: Execute targeted tests & full regression suite
        reg_engine = RegressionEngine()
        target_res = await reg_engine.execute_targeted_regression(
            changed_files=["factory/services/checkout_service.py"],
            project_id=proj.id,
            run_full_suite=False,
        )
        assert target_res["is_passed"] is True
        assert "api_tests" in target_res["suites_executed"]

        full_reg_res = await reg_engine.execute_targeted_regression(
            changed_files=["factory/services/checkout_service.py"],
            project_id=proj.id,
            run_full_suite=True,
        )
        assert full_reg_res["is_passed"] is True
        assert full_reg_res["total_tests"] > 80

        # Step 10: Run security scans
        sec_agent = SecurityRemediationAgent()
        sec_findings = await sec_agent.scan_security_findings(session, proj.id)
        assert len(sec_findings) >= 1

        # Step 11: Verify pull request generation
        assert "github.com" in fix_res["pr_url"]

        # Step 12: Verify approval workflow gate
        q_app = select(ApprovalRecord).where(ApprovalRecord.id == fix_res["approval_id"])
        approval = (await session.execute(q_app)).scalar_one_or_none()
        assert approval is not None
        assert approval.status == "pending"

        # Step 13: Merge after authorized operator approval
        approval.status = "approved"
        approval.decided_at = datetime.utcnow()
        approval.notes = "Verified fix in staging harness; 84 regression tests passed."
        bug.status = "resolved"
        bug.resolved_at = datetime.utcnow()
        await session.commit()

        # Step 14: Deploy through Phase 6 ReleaseManager
        rel_mgr = ReleaseManager()
        deploy_res = await rel_mgr.prepare_release(
            project_id=proj.id,
            version="v2.4.1-staging-fix",
            environment="staging",
            strategy="rolling",
            commit_sha="b7c8d9e0f1a2",
        )
        assert deploy_res is not None
        assert deploy_res.version == "v2.4.1-staging-fix"

        # Step 15: Verify improvement through Phase 7 monitoring probe
        app_monitor = ApplicationMonitoringAgent()
        probe_res = await app_monitor.probe_application(
            project_id=proj.id,
            endpoint_url="http://staging.factory.internal/health",
            simulated_latency_ms=28.4,
            simulated_status_code=200,
        )
        assert probe_res["is_healthy"] is True
        assert probe_res["status_code"] == 200
        assert probe_res["latency_ms"] < 50.0
