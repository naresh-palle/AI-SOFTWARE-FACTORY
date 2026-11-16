"""
Deployment and Release Management API Endpoints.
Provides deployment intelligence analysis, build registration, release orchestration,
smoke testing, automated rollback, and database migration governance.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import desc, func, select, and_

from factory.core.config import settings
from factory.core.database import get_db_session
from factory.core.logger import logger
from factory.models.schema import (
    ApprovalRecord,
    BuildArtifact,
    DatabaseMigrationRecord,
    DeploymentHistory,
    DeploymentRelease,
    EnvironmentConfig,
    Project,
    RollbackRecord,
)
from factory.deployment import (
    BuildManager,
    DatabaseMigrationAgent,
    DeploymentCostManager,
    DeploymentIntelligenceEngine,
    DnsSslManager,
    EnvironmentManager,
    ReleaseManager,
    RollbackEngine,
    SmokeTester,
)
from factory.orchestrator.master import project_workspace


router = APIRouter(prefix="/deployment", tags=["Deployment & Release Management"])
build_mgr = BuildManager()
env_mgr = EnvironmentManager()
mig_agent = DatabaseMigrationAgent()
rel_mgr = ReleaseManager()
rollback_eng = RollbackEngine()


# ==========================================
# Pydantic Schemas
# ==========================================

class BuildRequest(BaseModel):
    project_id: str
    version: str = "v1.0.0"
    commit_sha: Optional[str] = "0000000000000000000000000000000000000000"
    artifact_type: str = "docker_image"
    dependencies: List[str] = Field(default_factory=list)


class ReleasePrepareRequest(BaseModel):
    project_id: str
    version: str
    environment: str = "staging"  # development, testing, staging, production
    strategy: str = "rolling"  # rolling, blue_green, canary
    commit_sha: Optional[str] = "0000000000000000000000000000000000000000"
    build_artifact_id: Optional[str] = None
    target_type: str = "aws_ecs"


class DeployExecutionRequest(BaseModel):
    simulate_healthy: bool = True
    approved: bool = False


class RollbackRequest(BaseModel):
    project_id: str
    current_release_id: str
    reason: str
    trigger_type: str = "manual_operator"


class MigrationCreateRequest(BaseModel):
    project_id: str
    description: str
    sql_up: str
    sql_down: Optional[str] = None


class MigrationExecuteRequest(BaseModel):
    environment: str = "development"
    approved: bool = False


class DnsSslRequest(BaseModel):
    domain_name: str
    target_cname: str
    environment: str = "production"


# ==========================================
# Deployment Intelligence & Build APIs
# ==========================================

@router.get("/analysis/{project_id}")
async def analyze_project_deployment(project_id: str):
    """Analyze project workspace and dynamically determine optimal deployment architecture."""
    async with get_db_session() as session:
        q = select(Project).where(Project.id == project_id)
        project = (await session.execute(q)).scalar_one_or_none()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

    try:
        p_dir = project_workspace(project_id)
    except Exception:
        p_dir = settings.PROJECTS_STORAGE_DIR / project_id

    profile = DeploymentIntelligenceEngine.analyze_project(
        project_dir=p_dir,
        requirement_text=project.requirement_text or "",
        platform_target=project.platform_target or "fullstack",
    )
    return profile.model_dump()


@router.post("/build")
async def trigger_build_pipeline(req: BuildRequest):
    """Execute automated build pipeline, generate SBOM, scan container CVEs, and register BuildArtifact."""
    async with get_db_session() as session:
        q = select(Project).where(Project.id == req.project_id)
        proj = (await session.execute(q)).scalar_one_or_none()
        if not proj:
            raise HTTPException(status_code=404, detail="Project not found")

    artifact = await build_mgr.register_build_artifact(
        project_id=req.project_id,
        version=req.version,
        commit_sha=req.commit_sha or "0000000000000000000000000000000000000000",
        artifact_type=req.artifact_type,
        dependencies=req.dependencies,
    )

    return {
        "artifact_id": artifact.id,
        "build_id": artifact.build_id,
        "version": artifact.version,
        "image_tag": artifact.image_tag,
        "sha256": artifact.sha256,
        "status": artifact.status,
        "sbom_components_count": len(artifact.sbom_json.get("components", [])),
        "security_gate_passed": artifact.security_scan_summary.get("pass_gate", True),
    }


@router.get("/artifacts/{project_id}")
async def list_build_artifacts(project_id: str):
    """List all immutable build artifacts and vulnerability summaries for a project."""
    async with get_db_session() as session:
        q = select(BuildArtifact).where(BuildArtifact.project_id == project_id).order_by(desc(BuildArtifact.created_at))
        artifacts = (await session.execute(q)).scalars().all()
        return [
            {
                "id": a.id,
                "version": a.version,
                "build_id": a.build_id,
                "commit_sha": a.commit_sha,
                "image_tag": a.image_tag,
                "sha256": a.sha256,
                "size_bytes": a.size_bytes,
                "status": a.status,
                "security_scan": a.security_scan_summary,
                "created_at": a.created_at.isoformat(),
            }
            for a in artifacts
        ]


# ==========================================
# Release Management & Rollback APIs
# ==========================================

@router.post("/release/prepare")
async def prepare_release_endpoint(req: ReleasePrepareRequest):
    """Prepare a versioned release manifest with specified progressive delivery strategy."""
    release = await rel_mgr.prepare_release(
        project_id=req.project_id,
        version=req.version,
        environment=req.environment,
        strategy=req.strategy,
        commit_sha=req.commit_sha or "0000000000000000000000000000000000000000",
        build_artifact_id=req.build_artifact_id,
        target_type=req.target_type,
    )
    return {
        "release_id": release.id,
        "version": release.version,
        "environment": release.environment,
        "strategy": release.strategy,
        "status": release.status,
        "created_at": release.created_at.isoformat(),
    }


@router.post("/release/{release_id}/deploy")
async def execute_deployment_endpoint(release_id: str, req: DeployExecutionRequest):
    """
    Execute release deployment:
    1. Enforce human governance gate on production environment.
    2. Execute deployment steps.
    3. Run post-deployment smoke tests.
    4. Auto-rollback if smoke test fails.
    """
    async with get_db_session() as session:
        q = select(DeploymentRelease).where(DeploymentRelease.id == release_id)
        release = (await session.execute(q)).scalar_one_or_none()
        if not release:
            raise HTTPException(status_code=404, detail="Release not found")

        # Governance Check: Production requires explicit approval
        if release.environment == "production" and not req.approved:
            appr_q = (
                select(ApprovalRecord)
                .where(
                    and_(
                        ApprovalRecord.project_id == release.project_id,
                        ApprovalRecord.action_type == "production_deploy",
                        ApprovalRecord.status == "approved",
                    )
                )
                .order_by(desc(ApprovalRecord.created_at))
            )
            has_approval = (await session.execute(appr_q)).scalars().first()
            if not has_approval:
                logger.warning(f"Deployment: Production release {release.version} BLOCKED without approval.")
                return {
                    "success": False,
                    "status": "blocked_awaiting_approval",
                    "reason": "Production deployments strictly require human sign-off before rollout.",
                }

    # Execute Smoke Tests
    smoke = SmokeTester.run_smoke_tests(
        endpoint_url=release.endpoint_url or "https://app.factory.internal",
        simulated_healthy=req.simulate_healthy,
    )

    if smoke["overall_status"] != "PASSED":
        # Post-deployment validation failure: Trigger Automated Rollback!
        logger.error(f"Deployment: Smoke test FAILED for release {release.version}. Triggering automated rollback.")
        rollback_res = await rollback_eng.execute_rollback(
            project_id=release.project_id,
            current_release_id=release.id,
            reason=f"Automated rollback: {smoke.get('failure_reason')}",
            trigger_type="automated_health_failure",
        )
        return {
            "success": False,
            "status": "rolled_back",
            "smoke_tests": smoke,
            "rollback": rollback_res,
        }

    # Smoke tests passed: activate release and record in DeploymentHistory
    activated = await rel_mgr.activate_release(release.id, smoke_test_results=smoke)

    async with get_db_session() as session:
        history = DeploymentHistory(
            project_id=activated.project_id,
            environment=activated.environment,
            status="success",
            commit_sha=activated.commit_sha,
            endpoint_url=activated.endpoint_url,
            logs=f"Deployed {activated.version} ({activated.strategy}) successfully.",
            deployed_at=datetime.utcnow(),
        )
        session.add(history)
        await session.commit()

    return {
        "success": True,
        "status": "active",
        "release_id": activated.id,
        "version": activated.version,
        "environment": activated.environment,
        "endpoint_url": activated.endpoint_url,
        "smoke_tests": smoke,
    }


@router.post("/rollback")
async def trigger_manual_rollback(req: RollbackRequest):
    """Manually roll back to previous stable release."""
    res = await rollback_eng.execute_rollback(
        project_id=req.project_id,
        current_release_id=req.current_release_id,
        reason=req.reason,
        trigger_type=req.trigger_type,
    )
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("reason", "Rollback failed"))
    return res


@router.get("/releases/{project_id}")
async def list_project_releases(project_id: str):
    """List deployment releases for a project."""
    async with get_db_session() as session:
        q = (
            select(DeploymentRelease)
            .where(DeploymentRelease.project_id == project_id)
            .order_by(desc(DeploymentRelease.created_at))
        )
        releases = (await session.execute(q)).scalars().all()
        return [
            {
                "id": r.id,
                "version": r.version,
                "environment": r.environment,
                "strategy": r.strategy,
                "status": r.status,
                "is_current": r.is_current,
                "endpoint_url": r.endpoint_url,
                "commit_sha": r.commit_sha,
                "created_at": r.created_at.isoformat(),
                "deployed_at": r.deployed_at.isoformat() if r.deployed_at else None,
            }
            for r in releases
        ]


# ==========================================
# Database Migrations & Environment APIs
# ==========================================

@router.post("/migrations/create")
async def create_migration_endpoint(req: MigrationCreateRequest):
    """Create a database migration script and validate safety (destructive operations)."""
    record = await mig_agent.create_migration_script(
        project_id=req.project_id,
        description=req.description,
        sql_up=req.sql_up,
        sql_down=req.sql_down,
    )
    return {
        "migration_id": record.id,
        "version_num": record.version_num,
        "script_name": record.script_name,
        "is_destructive": record.is_destructive,
        "status": record.status,
    }


@router.post("/migrations/{migration_id}/execute")
async def execute_migration_endpoint(migration_id: str, req: MigrationExecuteRequest):
    """Execute a database migration script with safety guardrails."""
    res = await mig_agent.execute_migration(
        migration_id=migration_id,
        environment=req.environment,
        approved=req.approved,
    )
    return res


@router.get("/migrations/{project_id}")
async def list_migrations(project_id: str):
    """List database migrations and their execution status for a project."""
    async with get_db_session() as session:
        q = (
            select(DatabaseMigrationRecord)
            .where(DatabaseMigrationRecord.project_id == project_id)
            .order_by(desc(DatabaseMigrationRecord.created_at))
        )
        migrations = (await session.execute(q)).scalars().all()
        return [
            {
                "id": m.id,
                "version_num": m.version_num,
                "description": m.description,
                "script_name": m.script_name,
                "is_destructive": m.is_destructive,
                "backup_checkpoint": m.backup_checkpoint,
                "status": m.status,
                "created_at": m.created_at.isoformat(),
                "executed_at": m.executed_at.isoformat() if m.executed_at else None,
            }
            for m in migrations
        ]


@router.get("/environments/{project_id}")
async def get_environments(project_id: str):
    """Get configurations and secure secret references across all 4 environments."""
    envs = ["development", "testing", "staging", "production"]
    configs = []
    for e in envs:
        cfg = await env_mgr.get_or_create_env_config(project_id, e)
        configs.append({
            "environment": cfg.environment,
            "config_data": cfg.config_data,
            "secret_references": cfg.secret_references,
            "cpu_limits": cfg.cpu_limits,
            "memory_limits": cfg.memory_limits,
            "min_replicas": cfg.min_replicas,
            "max_replicas": cfg.max_replicas,
        })
    return configs


@router.post("/dns-ssl")
async def configure_dns_ssl(req: DnsSslRequest):
    """Generate Route 53 DNS and ACM certificate manifests with production governance."""
    return DnsSslManager.generate_dns_and_ssl_manifest(
        domain_name=req.domain_name,
        target_cname=req.target_cname,
        environment=req.environment,
    )


@router.get("/status")
async def get_deployment_overview_status():
    """Aggregated status across deployments, environments, active versions, and costs."""
    async with get_db_session() as session:
        total_deploys = (await session.execute(select(func.count(DeploymentHistory.id)))).scalar() or 0
        total_releases = (await session.execute(select(func.count(DeploymentRelease.id)))).scalar() or 0
        total_artifacts = (await session.execute(select(func.count(BuildArtifact.id)))).scalar() or 0
        total_rollbacks = (await session.execute(select(func.count(RollbackRecord.id)))).scalar() or 0

    cost_est = DeploymentCostManager.estimate_deployment_cost()

    return {
        "summary": {
            "total_deployments": total_deploys,
            "total_releases": total_releases,
            "total_build_artifacts": total_artifacts,
            "total_rollbacks": total_rollbacks,
        },
        "environments": [
            {"name": "Development", "status": "Active", "type": "Local Container", "url": "http://localhost:8000"},
            {"name": "Testing", "status": "Ready", "type": "Automated Ephemeral", "url": "http://test.factory.internal"},
            {"name": "Staging", "status": "Active", "type": "AWS ECS Fargate", "url": "https://staging.factory.app"},
            {"name": "Production", "status": "Gated", "type": "AWS ECS Fargate (Multi-AZ)", "url": "https://app.factory.app"},
        ],
        "cost_estimate": cost_est,
        "supported_strategies": ["rolling", "blue_green", "canary"],
    }
