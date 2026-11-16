"""
Comprehensive Test Suite for Autonomous Deployment & Release Management Engine.
Validates:
- Deployment Intelligence Engine architecture selection (ECS vs S3+CloudFront vs K8s vs Mobile)
- Multi-stage Dockerfile generation, SBOM creation, and container vulnerability scanning
- Immutable BuildArtifact registration and SHA-256 verification
- Environment configurations and secret reference hygiene
- Database migration safety (destructive DROP detection, backup checkpoints, production gates)
- Release management with progressive rollout strategies (Rolling, Blue-Green, Canary)
- Automated rollback execution triggered by post-deployment smoke test failures
- Manual rollback to previous stable release
- Post-deployment smoke tests and health checks
- Route 53 DNS and ACM SSL certificate manifests
- Deployment cost and FinOps estimation
- REST API contracts across all /api/v1/deployment endpoints
"""

import os
import tempfile
from datetime import datetime
from pathlib import Path
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select

from factory.api.main import app
from factory.core.database import get_db_session, init_db
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
from factory.deployment.targets.aws_agent import AWSTargetAgent
from factory.deployment.targets.k8s_agent import KubernetesTargetAgent
from factory.deployment.targets.mobile_agent import MobileReleaseAgent


@pytest.fixture(autouse=True)
async def setup_test_db():
    await init_db()
    yield


@pytest.mark.asyncio
async def test_deployment_intelligence_architecture_selection():
    with tempfile.TemporaryDirectory() as tmpdir:
        p_path = Path(tmpdir)

        # 1. Test Static Website
        (p_path / "package.json").write_text('{"name": "landing", "dependencies": {"react": "^18"}}')
        profile_static = DeploymentIntelligenceEngine.analyze_project(
            p_path, requirement_text="Simple static landing page for SaaS", platform_target="website"
        )
        assert profile_static.target_architecture == "aws_s3_cloudfront"
        assert profile_static.container_required is False
        assert profile_static.estimated_monthly_cost_usd <= 10.0

        # 2. Test High-Scale Kubernetes / Microservices
        profile_k8s = DeploymentIntelligenceEngine.analyze_project(
            p_path, requirement_text="Distributed microservices architecture with kubernetes and redis cache", platform_target="fullstack"
        )
        assert profile_k8s.target_architecture == "kubernetes"
        assert profile_k8s.recommended_strategy == "canary"
        assert profile_k8s.container_required is True

        # 3. Test Mobile Application Target
        profile_mobile = DeploymentIntelligenceEngine.analyze_project(
            p_path, requirement_text="Cross-platform iOS and Android e-commerce application", platform_target="mobile"
        )
        assert profile_mobile.target_architecture == "mobile_release"
        assert "MOBILE_SIGNING_KEYSTORE" in profile_mobile.secrets_required

        # 4. Test Standard Full-Stack Web App (Default to AWS ECS Fargate)
        (p_path / "requirements.txt").write_text("fastapi>=0.110.0\nuvicorn>=0.28.0")
        profile_ecs = DeploymentIntelligenceEngine.analyze_project(
            p_path, requirement_text="Enterprise CRM and backend API with PostgreSQL database", platform_target="fullstack"
        )
        assert profile_ecs.target_architecture == "aws_ecs_fargate"
        assert profile_ecs.recommended_strategy == "rolling"
        assert profile_ecs.database_required == "PostgreSQL"


@pytest.mark.asyncio
async def test_build_manager_and_immutable_artifacts():
    build_mgr = BuildManager()

    # 1. Multi-stage Dockerfile generation
    dockerfile_py = build_mgr.generate_multistage_dockerfile("fullstack_web_api")
    assert "FROM python:3.10-slim AS builder" in dockerfile_py
    assert "USER appuser" in dockerfile_py
    assert "HEALTHCHECK" in dockerfile_py

    dockerfile_node = build_mgr.generate_multistage_dockerfile("nextjs")
    assert "FROM node:20-alpine AS builder" in dockerfile_node
    assert "USER nextjs" in dockerfile_node

    # 2. SBOM Generation (CycloneDX format)
    sbom = build_mgr.generate_sbom("proj-123", "v1.0.0", ["fastapi>=0.110.0", "pydantic>=2.6.0"])
    assert sbom["bomFormat"] == "CycloneDX"
    assert len(sbom["components"]) == 2

    # 3. Vulnerability Scan
    scan = build_mgr.scan_container_vulnerabilities("ai-factory:v1.0.0")
    assert scan["pass_gate"] is True
    assert scan["vulnerabilities"]["CRITICAL"] == 0

    # 4. Register BuildArtifact in DB
    async with get_db_session() as session:
        proj = Project(name="Build App", requirement_text="App with build", status="initialized")
        session.add(proj)
        await session.commit()
        await session.refresh(proj)
        p_id = proj.id

    artifact = await build_mgr.register_build_artifact(
        project_id=p_id,
        version="v1.0.0",
        commit_sha="a1b2c3d4e5f678901234567890abcdef12345678",
    )
    assert artifact.id is not None
    assert artifact.version == "v1.0.0"
    assert artifact.status == "ready"
    assert len(artifact.sha256) == 64


@pytest.mark.asyncio
async def test_environment_configuration_and_secret_hygiene():
    env_mgr = EnvironmentManager()

    async with get_db_session() as session:
        proj = Project(name="Env App", requirement_text="App with envs", status="initialized")
        session.add(proj)
        await session.commit()
        await session.refresh(proj)
        project_id = proj.id

    # Get configs for staging and production
    cfg_staging = await env_mgr.get_or_create_env_config(project_id, "staging")
    cfg_prod = await env_mgr.get_or_create_env_config(project_id, "production")

    assert cfg_staging.environment == "staging"
    assert cfg_prod.environment == "production"

    # Secret references must point to Secrets Manager, never plaintext secrets
    assert "arn:aws:secretsmanager" in cfg_prod.secret_references["DATABASE_URL"]
    assert "arn:aws:secretsmanager" in cfg_prod.secret_references["SECRET_KEY"]

    # Production must have higher resources
    assert cfg_prod.min_replicas >= cfg_staging.min_replicas

    # Compare environments
    diff = env_mgr.compare_environments(cfg_staging, cfg_prod)
    assert diff["source_env"] == "staging"
    assert diff["target_env"] == "production"


@pytest.mark.asyncio
async def test_database_migration_agent_safety_guardrails():
    mig_agent = DatabaseMigrationAgent()

    # 1. Safe additive migration
    safe_sql = "ALTER TABLE users ADD COLUMN phone_number VARCHAR(20);"
    assert mig_agent.is_destructive(safe_sql) is False

    # 2. Destructive migrations
    drop_table_sql = "DROP TABLE deprecated_logs;"
    drop_col_sql = "ALTER TABLE orders DROP COLUMN legacy_discount;"
    assert mig_agent.is_destructive(drop_table_sql) is True
    assert mig_agent.is_destructive(drop_col_sql) is True

    # 3. Create and execute migration
    async with get_db_session() as session:
        proj = Project(name="Mig App", requirement_text="App with mig", status="initialized")
        session.add(proj)
        await session.commit()
        await session.refresh(proj)
        p_id = proj.id

    rec = await mig_agent.create_migration_script(
        project_id=p_id,
        description="Drop legacy table",
        sql_up=drop_table_sql,
    )
    assert rec.is_destructive is True

    # Destructive migration on production without approval must be blocked!
    res_blocked = await mig_agent.execute_migration(rec.id, environment="production", approved=False)
    assert res_blocked["success"] is False
    assert res_blocked["status"] == "blocked_requires_approval"

    # With approval, migration executes and records backup checkpoint
    res_approved = await mig_agent.execute_migration(rec.id, environment="production", approved=True)
    assert res_approved["success"] is True
    assert "backup_" in res_approved["backup_checkpoint"]


@pytest.mark.asyncio
async def test_release_management_and_automated_rollback():
    rel_mgr = ReleaseManager()
    rollback_eng = RollbackEngine()

    async with get_db_session() as session:
        proj = Project(name="Release App", requirement_text="App with release", status="initialized")
        session.add(proj)
        await session.commit()
        await session.refresh(proj)
        p_id = proj.id

    # 1. Deploy stable release v1.0.0
    r1 = await rel_mgr.prepare_release(project_id=p_id, version="v1.0.0", environment="production")
    await rel_mgr.activate_release(r1.id, smoke_test_results={"overall_status": "PASSED"})

    # 2. Prepare candidate release v1.1.0
    r2 = await rel_mgr.prepare_release(project_id=p_id, version="v1.1.0", environment="production")

    # 3. Simulate post-deployment smoke test failure on v1.1.0
    smoke_fail = SmokeTester.run_smoke_tests("https://app.factory.internal", simulated_healthy=False)
    assert smoke_fail["overall_status"] == "FAILED"

    # Automated rollback restores v1.0.0
    rollback_res = await rollback_eng.execute_rollback(
        project_id=p_id,
        current_release_id=r2.id,
        reason=smoke_fail["failure_reason"],
        trigger_type="automated_health_failure",
    )
    assert rollback_res["success"] is True
    assert rollback_res["from_version"] == "v1.1.0"
    assert rollback_res["to_version"] == "v1.0.0"

    # Verify RollbackRecord exists in DB
    async with get_db_session() as session:
        q = select(RollbackRecord).where(RollbackRecord.project_id == p_id)
        rec = (await session.execute(q)).scalar_one_or_none()
        assert rec is not None
        assert rec.trigger_type == "automated_health_failure"


@pytest.mark.asyncio
async def test_target_agents_manifest_generation():
    # 1. AWS Agent
    task_def = AWSTargetAgent.generate_fargate_task_def(
        app_name="web-service",
        image_tag="123456789.dkr.ecr.us-east-1.amazonaws.com/web:v1.0.0",
        cpu=1024,
        memory=2048,
    )
    assert task_def["requiresCompatibilities"] == ["FARGATE"]
    assert task_def["containerDefinitions"][0]["name"] == "web-service"

    # 2. Kubernetes Agent
    k8s = KubernetesTargetAgent.generate_k8s_manifests(
        app_name="microservice-api",
        image_tag="k8s-repo/api:v1.0.0",
        replicas=3,
        strategy="rolling",
    )
    assert "kind: Deployment" in k8s["all_in_one_manifest"]
    assert "kind: Ingress" in k8s["all_in_one_manifest"]
    assert "kind: HorizontalPodAutoscaler" in k8s["all_in_one_manifest"]

    # 3. Mobile Release Agent
    mobile = MobileReleaseAgent.prepare_mobile_release(
        app_name="FactoryMobile",
        bundle_id="com.factory.mobile",
        version="1.0.0",
        platform="android",
    )
    assert mobile["governance"]["requires_explicit_human_approval"] is True


@pytest.mark.asyncio
async def test_dns_ssl_and_cost_estimation():
    # DNS & SSL
    manifest = DnsSslManager.generate_dns_and_ssl_manifest(
        domain_name="app.factory.com",
        target_cname="app-alb-123.us-east-1.elb.amazonaws.com",
        environment="production",
    )
    assert manifest["https_enforced"] is True
    assert manifest["governance"]["requires_human_approval"] is True

    # Cost Estimation
    cost_ecs = DeploymentCostManager.estimate_deployment_cost("aws_ecs_fargate", replicas=2)
    assert cost_ecs["monthly_total_usd"] == 60.0
    cost_s3 = DeploymentCostManager.estimate_deployment_cost("aws_s3_cloudfront")
    assert cost_s3["monthly_total_usd"] == 5.0


@pytest.mark.asyncio
async def test_deployment_api_endpoints_full_e2e():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Create dummy project
        async with get_db_session() as session:
            proj = Project(name="E2E Deploy App", requirement_text="Full-stack FastAPI with Postgres", status="initialized")
            session.add(proj)
            await session.commit()
            await session.refresh(proj)
            p_id = proj.id

        # 1. Analyze deployment architecture
        an_res = await client.get(f"/api/v1/deployment/analysis/{p_id}")
        assert an_res.status_code == 200
        assert "target_architecture" in an_res.json()

        # 2. Trigger build pipeline
        b_res = await client.post(
            "/api/v1/deployment/build",
            json={"project_id": p_id, "version": "v1.0.0"},
        )
        assert b_res.status_code == 200
        assert b_res.json()["status"] == "ready"
        artifact_id = b_res.json()["artifact_id"]

        # 3. List artifacts
        art_res = await client.get(f"/api/v1/deployment/artifacts/{p_id}")
        assert art_res.status_code == 200
        assert len(art_res.json()) >= 1

        # 4. Prepare staging release
        prep_res = await client.post(
            "/api/v1/deployment/release/prepare",
            json={
                "project_id": p_id,
                "version": "v1.0.0",
                "environment": "staging",
                "strategy": "rolling",
                "build_artifact_id": artifact_id,
            },
        )
        assert prep_res.status_code == 200
        release_id = prep_res.json()["release_id"]

        # 5. Deploy release to staging
        dep_res = await client.post(
            f"/api/v1/deployment/release/{release_id}/deploy",
            json={"simulate_healthy": True, "approved": False},
        )
        assert dep_res.status_code == 200
        assert dep_res.json()["status"] == "active"
        assert dep_res.json()["smoke_tests"]["overall_status"] == "PASSED"

        # 6. List environments
        env_res = await client.get(f"/api/v1/deployment/environments/{p_id}")
        assert env_res.status_code == 200
        assert len(env_res.json()) == 4

        # 7. Create & list migrations
        mig_res = await client.post(
            "/api/v1/deployment/migrations/create",
            json={
                "project_id": p_id,
                "description": "Add user avatar column",
                "sql_up": "ALTER TABLE users ADD COLUMN avatar_url VARCHAR(255);",
            },
        )
        assert mig_res.status_code == 200
        assert mig_res.json()["is_destructive"] is False

        list_mig = await client.get(f"/api/v1/deployment/migrations/{p_id}")
        assert list_mig.status_code == 200
        assert len(list_mig.json()) >= 1

        # 8. Overall deployment status
        stat_res = await client.get("/api/v1/deployment/status")
        assert stat_res.status_code == 200
        assert "summary" in stat_res.json()
        assert "environments" in stat_res.json()
