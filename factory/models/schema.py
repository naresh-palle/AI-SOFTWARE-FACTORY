"""
Centralized Factory Database Schema.
Defines all entities required for the Autonomous AI Software Development Factory.
"""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Table,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


def generate_uuid() -> str:
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=True)
    role = Column(String(50), default="developer")  # admin, architect, developer
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    projects = relationship("Project", back_populates="owner")
    approvals = relationship("ApprovalRecord", back_populates="approver")


class Project(Base):
    __tablename__ = "projects"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    requirement_text = Column(Text, nullable=False)
    platform_target = Column(String(100), default="fullstack")  # website, android, ios, combined, fullstack
    execution_mode = Column(String(50), default="autonomous")  # assisted, semi-autonomous, autonomous
    status = Column(String(50), default="initialized")  # initialized, planning, in_progress, awaiting_approval, completed, failed
    current_stage = Column(Integer, default=1)  # 1 to 23
    owner_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    owner = relationship("User", back_populates="projects")
    requirements = relationship("ProjectRequirement", back_populates="project", cascade="all, delete-orphan")
    architecture = relationship("ProjectArchitecture", back_populates="project", uselist=False, cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="project", cascade="all, delete-orphan")
    executions = relationship("AgentExecutionHistory", back_populates="project", cascade="all, delete-orphan")
    repo = relationship("GitHubRepositoryRecord", back_populates="project", uselist=False, cascade="all, delete-orphan")
    integrations = relationship("ExternalIntegration", back_populates="project", cascade="all, delete-orphan")
    test_results = relationship("TestingResult", back_populates="project", cascade="all, delete-orphan")
    security_findings = relationship("SecurityFinding", back_populates="project", cascade="all, delete-orphan")
    deployments = relationship("DeploymentHistory", back_populates="project", cascade="all, delete-orphan")
    approvals = relationship("ApprovalRecord", back_populates="project", cascade="all, delete-orphan")
    costs = relationship("CostRecord", back_populates="project", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="project", cascade="all, delete-orphan")


class ProjectRequirement(Base):
    __tablename__ = "project_requirements"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False, index=True)
    raw_requirement = Column(Text, nullable=False)
    functional_specs = Column(JSON, default=dict)
    business_objectives = Column(JSON, default=list)
    identified_features = Column(JSON, default=list)
    constraints = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="requirements")


class ProjectArchitecture(Base):
    __tablename__ = "project_architectures"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False, unique=True)
    frontend_stack = Column(String(255), nullable=True)
    backend_stack = Column(String(255), nullable=True)
    mobile_stack = Column(String(255), nullable=True)
    database_stack = Column(String(255), nullable=True)
    cache_stack = Column(String(255), nullable=True)
    cloud_stack = Column(String(255), nullable=True)
    ci_cd_stack = Column(String(255), nullable=True)
    selected_agents = Column(JSON, default=list)
    mermaid_diagram = Column(Text, nullable=True)
    estimated_cost_usd = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="architecture")


class AgentRegistryRecord(Base):
    __tablename__ = "agent_registry"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    role_number = Column(Integer, unique=True, nullable=False)  # 1 to 97
    name = Column(String(100), unique=True, nullable=False)
    role_title = Column(String(150), nullable=False)
    category = Column(String(100), nullable=False)  # Product, UI/UX, Backend, Database, Social/API, Auth, Security, DevOps, QA, Maintenance
    description = Column(Text, nullable=False)
    capabilities = Column(JSON, default=list)
    is_active = Column(Boolean, default=True)


class AgentConfiguration(Base):
    __tablename__ = "agent_configurations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False)
    agent_name = Column(String(100), nullable=False)
    model_provider = Column(String(50), default="default")
    model_name = Column(String(100), nullable=True)
    system_prompt_override = Column(Text, nullable=True)
    parameters = Column(JSON, default=dict)


class Task(Base):
    __tablename__ = "tasks"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False, index=True)
    stage = Column(Integer, nullable=False)
    agent_name = Column(String(100), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(50), default="pending")  # pending, in_progress, completed, failed, blocked
    input_payload = Column(JSON, default=dict)
    output_payload = Column(JSON, default=dict)
    execution_evidence = Column(Text, nullable=True)  # File path, commit SHA, test run ID
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    project = relationship("Project", back_populates="tasks")
    dependencies = relationship(
        "TaskDependency",
        foreign_keys="TaskDependency.task_id",
        back_populates="task",
        cascade="all, delete-orphan",
    )


class TaskDependency(Base):
    __tablename__ = "task_dependencies"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    task_id = Column(String(36), ForeignKey("tasks.id"), nullable=False)
    depends_on_task_id = Column(String(36), ForeignKey("tasks.id"), nullable=False)

    task = relationship("Task", foreign_keys=[task_id], back_populates="dependencies")


class AgentExecutionHistory(Base):
    __tablename__ = "agent_execution_history"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False, index=True)
    task_id = Column(String(36), ForeignKey("tasks.id"), nullable=True)
    agent_name = Column(String(100), nullable=False)
    status = Column(String(50), nullable=False)
    latency_ms = Column(Integer, default=0)
    input_tokens = Column(Integer, default=0)
    output_tokens = Column(Integer, default=0)
    evidence_log = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="executions")


class GitHubRepositoryRecord(Base):
    __tablename__ = "github_repositories"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False, unique=True)
    repo_name = Column(String(255), nullable=False)
    repo_url = Column(String(500), nullable=False)
    default_branch = Column(String(100), default="main")
    current_branch = Column(String(100), default="main")
    latest_commit_hash = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="repo")


class ExternalIntegration(Base):
    __tablename__ = "external_integrations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False)
    provider = Column(String(100), nullable=False)  # meta, youtube, x, stripe, aws, etc.
    integration_type = Column(String(100), nullable=False)
    config_json = Column(JSON, default=dict)
    is_active = Column(Boolean, default=True)

    project = relationship("Project", back_populates="integrations")


class DeveloperAccountReference(Base):
    __tablename__ = "developer_account_references"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    account_type = Column(String(50), nullable=False)  # factory_owner, tenant_customer
    platform = Column(String(50), nullable=False)  # meta, google, x, aws
    account_identifier = Column(String(255), nullable=False)
    encrypted_credentials = Column(Text, nullable=True)
    permissions = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)


class OAuthConnection(Base):
    __tablename__ = "oauth_connections"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    tenant_id = Column(String(100), nullable=False, index=True)
    provider = Column(String(50), nullable=False)  # facebook, instagram, whatsapp, google, youtube, x, linkedin, tiktok
    account_type = Column(String(50), default="customer")  # factory_owner, customer
    user_identifier = Column(String(255), nullable=False)
    account_name = Column(String(255), nullable=True)
    encrypted_access_token = Column(Text, nullable=False)
    encrypted_refresh_token = Column(Text, nullable=True)
    token_expires_at = Column(DateTime, nullable=True)
    granted_scopes = Column(JSON, default=list)
    status = Column(String(50), default="active")  # active, expired, revoked
    rate_limit_remaining = Column(Integer, default=1000)
    last_refreshed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class DeveloperApplication(Base):
    __tablename__ = "developer_applications"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    developer_account_id = Column(String(36), ForeignKey("developer_account_references.id"), nullable=True)
    platform = Column(String(50), nullable=False)  # meta, google, x, linkedin, tiktok
    app_id = Column(String(100), nullable=False, unique=True, index=True)
    app_name = Column(String(255), nullable=False)
    app_type = Column(String(50), default="business")  # business, consumer, gaming
    status = Column(String(50), default="configured")  # configured, tested, pending_approval, approved, rejected
    client_id = Column(String(255), nullable=True)
    encrypted_client_secret = Column(Text, nullable=True)
    webhook_url = Column(String(500), nullable=True)
    verify_token = Column(String(255), nullable=True)
    privacy_policy_url = Column(String(500), nullable=True)
    data_deletion_url = Column(String(500), nullable=True)
    redirect_uris = Column(JSON, default=list)
    enabled_products = Column(JSON, default=list)  # facebook_login, instagram_graph, whatsapp_business, messenger, threads, youtube, x, linkedin, tiktok
    app_review_status = Column(JSON, default=dict)
    permissions_tracked = Column(JSON, default=list)
    rate_limit_tier = Column(String(50), default="standard")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SocialPlatformCatalog(Base):
    __tablename__ = "social_platform_catalog"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    platform_key = Column(String(50), unique=True, nullable=False, index=True)  # meta, facebook, instagram, whatsapp, messenger, threads, youtube, google, x, linkedin, tiktok
    display_name = Column(String(100), nullable=False)
    category = Column(String(50), nullable=False)  # meta, google, other
    supported_features = Column(JSON, default=list)
    auth_type = Column(String(50), default="oauth2")  # oauth2, pkce, api_key
    api_version = Column(String(20), default="v1")
    doc_url = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True)


class SocialAppReview(Base):
    __tablename__ = "social_app_reviews"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    app_id = Column(String(100), nullable=False, index=True)
    platform = Column(String(50), nullable=False)
    submission_type = Column(String(100), default="permissions")  # permissions, business_verification, use_case
    requested_permissions = Column(JSON, default=list)
    status = Column(String(50), default="draft")  # draft, submitted, in_review, approved, rejected
    reviewer_feedback = Column(Text, nullable=True)
    submission_notes = Column(Text, nullable=True)
    submitted_at = Column(DateTime, nullable=True)
    decided_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class SocialIntegrationLog(Base):
    __tablename__ = "social_integration_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), nullable=True, index=True)
    tenant_id = Column(String(100), nullable=False, default="default", index=True)
    platform = Column(String(50), nullable=False, index=True)
    endpoint = Column(String(255), nullable=False)
    method = Column(String(10), default="GET")
    status_code = Column(Integer, default=200)
    latency_ms = Column(Integer, default=0)
    success = Column(Boolean, default=True)
    error_message = Column(Text, nullable=True)
    request_id = Column(String(100), nullable=True)
    audit_actor = Column(String(100), default="SocialIntegrationEngine")
    created_at = Column(DateTime, default=datetime.utcnow)


class SocialApiError(Base):
    __tablename__ = "social_api_errors"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    platform = Column(String(50), nullable=False, index=True)
    error_code = Column(String(100), nullable=False)
    error_subcode = Column(String(100), nullable=True)
    error_message = Column(Text, nullable=False)
    error_type = Column(String(100), nullable=True)
    resolution_guidance = Column(Text, nullable=True)
    occurrences_count = Column(Integer, default=1)
    last_occurred_at = Column(DateTime, default=datetime.utcnow)


class AccountConnectionHistory(Base):
    __tablename__ = "account_connection_history"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    tenant_id = Column(String(100), nullable=False, index=True)
    platform = Column(String(50), nullable=False)
    user_identifier = Column(String(255), nullable=False)
    action = Column(String(50), nullable=False)  # connected, token_refreshed, scope_updated, disconnected, revoked
    actor = Column(String(100), default="system")
    details_json = Column(JSON, default=dict)
    timestamp = Column(DateTime, default=datetime.utcnow)


class WebhookSubscription(Base):
    __tablename__ = "webhook_subscriptions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False)
    platform = Column(String(50), nullable=False)
    callback_url = Column(String(500), nullable=False)
    verify_token = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)


class TestingResult(Base):
    __tablename__ = "testing_results"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False)
    test_suite = Column(String(100), nullable=False)  # unit, api, integration, ui, performance, security
    total_tests = Column(Integer, default=0)
    passed_tests = Column(Integer, default=0)
    failed_tests = Column(Integer, default=0)
    evidence_path = Column(String(500), nullable=True)
    details = Column(JSON, default=dict)
    executed_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="test_results")


class SecurityFinding(Base):
    __tablename__ = "security_findings"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False)
    severity = Column(String(50), nullable=False)  # low, medium, high, critical
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    tool = Column(String(100), default="factory_scanner")  # trivy, sonarqube, bandit
    remediation_status = Column(String(50), default="open")  # open, fixed, accepted_risk
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="security_findings")


class DeploymentHistory(Base):
    __tablename__ = "deployment_history"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False)
    environment = Column(String(50), nullable=False)  # dev, staging, prod
    status = Column(String(50), nullable=False)  # success, failed, pending
    commit_sha = Column(String(100), nullable=True)
    endpoint_url = Column(String(500), nullable=True)
    logs = Column(Text, nullable=True)
    deployed_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="deployments")


class ApprovalRecord(Base):
    __tablename__ = "approval_records"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False)
    stage = Column(Integer, nullable=False)
    action_type = Column(String(100), nullable=False)  # paid_service, production_deploy, legal_declaration, etc.
    description = Column(Text, nullable=False)
    status = Column(String(50), default="pending")  # pending, approved, rejected
    approver_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    decided_at = Column(DateTime, nullable=True)

    project = relationship("Project", back_populates="approvals")
    approver = relationship("User", back_populates="approvals")


class CostRecord(Base):
    __tablename__ = "cost_records"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False)
    category = Column(String(100), nullable=False)  # llm_tokens, cloud_infra, third_party_api
    amount_usd = Column(Float, nullable=False)
    details = Column(JSON, default=dict)
    recorded_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="costs")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=True)
    action = Column(String(100), nullable=False)
    actor = Column(String(100), nullable=False)
    details_json = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="audit_logs")


# ==========================================
# Cloud Worker & Persistent Workflow Entities
# ==========================================

class WorkerNode(Base):
    __tablename__ = "worker_nodes"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    worker_name = Column(String(100), unique=True, nullable=False)
    hostname = Column(String(255), nullable=True)
    ip_address = Column(String(64), nullable=True)
    status = Column(String(50), default="registered")  # registered, idle, busy, unhealthy, draining, terminated
    cpu_cores = Column(Integer, default=2)
    memory_mb = Column(Integer, default=4096)
    current_job_id = Column(String(36), nullable=True)
    last_heartbeat = Column(DateTime, default=datetime.utcnow)
    registered_at = Column(DateTime, default=datetime.utcnow)
    total_jobs_completed = Column(Integer, default=0)
    tags = Column(JSON, default=dict)


class WorkflowJob(Base):
    __tablename__ = "workflow_jobs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False, index=True)
    job_type = Column(String(50), default="full_pipeline")  # full_pipeline, single_stage, code_generation
    status = Column(String(50), default="queued")  # queued, assigned, running, paused, blocked_on_approval, completed, failed, cancelled
    priority = Column(Integer, default=5)  # 1 to 10
    current_stage = Column(Integer, default=1)
    target_stage = Column(Integer, default=23)
    assigned_worker_id = Column(String(36), ForeignKey("worker_nodes.id"), nullable=True)
    lease_expires_at = Column(DateTime, nullable=True)
    timeout_seconds = Column(Integer, default=3600)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    backoff_multiplier = Column(Float, default=2.0)
    idempotency_key = Column(String(128), unique=True, nullable=True, index=True)
    error_message = Column(Text, nullable=True)
    checkpoint_data = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    project = relationship("Project")
    worker = relationship("WorkerNode")
    checkpoints = relationship("WorkflowCheckpoint", back_populates="job", cascade="all, delete-orphan")


class WorkflowCheckpoint(Base):
    __tablename__ = "workflow_checkpoints"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    job_id = Column(String(36), ForeignKey("workflow_jobs.id"), nullable=False, index=True)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False, index=True)
    stage_number = Column(Integer, nullable=False)
    stage_title = Column(String(255), nullable=False)
    status = Column(String(50), default="completed")  # completed, failed, blocked_on_approval
    evidence_json = Column(JSON, default=list)
    artifacts_json = Column(JSON, default=dict)
    duration_ms = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    job = relationship("WorkflowJob", back_populates="checkpoints")
    project = relationship("Project")


class DeadLetterJob(Base):
    __tablename__ = "dead_letter_jobs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    original_job_id = Column(String(36), nullable=False, index=True)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False)
    failure_reason = Column(Text, nullable=False)
    error_details = Column(JSON, default=dict)
    attempts_made = Column(Integer, default=3)
    last_attempt_at = Column(DateTime, default=datetime.utcnow)
    resolved = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project")


# ==========================================
# Deployment & Release Management Entities
# ==========================================

class BuildArtifact(Base):
    __tablename__ = "build_artifacts"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False, index=True)
    version = Column(String(50), nullable=False)  # e.g. v1.0.0
    build_id = Column(String(100), nullable=False, index=True)
    commit_sha = Column(String(100), nullable=False)
    artifact_type = Column(String(50), nullable=False)  # docker_image, tar_gz_bundle, mobile_bundle, static_web
    artifact_url = Column(String(500), nullable=False)
    image_tag = Column(String(255), nullable=True)
    sbom_json = Column(JSON, default=dict)
    security_scan_summary = Column(JSON, default=dict)
    size_bytes = Column(Integer, default=0)
    sha256 = Column(String(64), nullable=False)
    status = Column(String(50), default="ready")  # building, ready, failed, scanned
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project")


class DeploymentRelease(Base):
    __tablename__ = "deployment_releases"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False, index=True)
    version = Column(String(50), nullable=False)
    environment = Column(String(50), nullable=False)  # development, testing, staging, production
    strategy = Column(String(50), default="rolling")  # rolling, blue_green, canary
    status = Column(String(50), default="prepared")  # prepared, pending_approval, deploying, active, rolled_back, failed
    build_artifact_id = Column(String(36), ForeignKey("build_artifacts.id"), nullable=True)
    commit_sha = Column(String(100), nullable=False)
    endpoint_url = Column(String(500), nullable=True)
    target_type = Column(String(50), default="aws_ecs")  # aws_ecs, aws_s3_cloudfront, kubernetes, mobile_store
    manifests_json = Column(JSON, default=dict)
    health_check_summary = Column(JSON, default=dict)
    deployed_by = Column(String(100), default="autonomous_agent")
    is_current = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    deployed_at = Column(DateTime, nullable=True)

    project = relationship("Project")
    build_artifact = relationship("BuildArtifact")


class DatabaseMigrationRecord(Base):
    __tablename__ = "database_migrations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False, index=True)
    version_num = Column(String(50), nullable=False)
    description = Column(String(255), nullable=False)
    script_name = Column(String(255), nullable=False)
    sql_up = Column(Text, nullable=False)
    sql_down = Column(Text, nullable=True)
    is_destructive = Column(Boolean, default=False)
    backup_checkpoint = Column(String(255), nullable=True)
    status = Column(String(50), default="pending")  # pending, approved, executed, rolled_back, failed
    executed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project")


class EnvironmentConfig(Base):
    __tablename__ = "environment_configs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False, index=True)
    environment = Column(String(50), nullable=False)  # development, testing, staging, production
    config_data = Column(JSON, default=dict)
    secret_references = Column(JSON, default=dict)  # Pointers to Secrets Manager, never plaintext
    cpu_limits = Column(String(50), default="1024m")
    memory_limits = Column(String(50), default="2048Mi")
    min_replicas = Column(Integer, default=1)
    max_replicas = Column(Integer, default=5)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    project = relationship("Project")


class RollbackRecord(Base):
    __tablename__ = "rollback_records"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False, index=True)
    from_release_id = Column(String(36), ForeignKey("deployment_releases.id"), nullable=False)
    to_release_id = Column(String(36), ForeignKey("deployment_releases.id"), nullable=False)
    reason = Column(String(500), nullable=False)
    trigger_type = Column(String(50), default="automated_health_failure")  # automated_health_failure, manual_operator
    status = Column(String(50), default="completed")  # initiated, completed, failed
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project")


# ==========================================
# Observability, AIOps & Self-Healing Entities
# ==========================================

class TelemetryMetricRecord(Base):
    __tablename__ = "telemetry_metrics"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False, index=True)
    metric_name = Column(String(100), nullable=False, index=True)
    metric_value = Column(Float, nullable=False)
    unit = Column(String(50), default="count")
    dimensions = Column(JSON, default=dict)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    project = relationship("Project")


class AlertRule(Base):
    __tablename__ = "alert_rules"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False, index=True)
    name = Column(String(150), nullable=False)
    metric_name = Column(String(100), nullable=False)
    condition = Column(String(20), default=">")  # >, <, >=, <=, ==
    threshold = Column(Float, nullable=False)
    duration_seconds = Column(Integer, default=60)
    severity = Column(String(50), default="medium")  # info, low, medium, high, critical
    is_enabled = Column(Boolean, default=True)
    notification_channels = Column(JSON, default=list)  # webhook, slack, email
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project")
    events = relationship("AlertEvent", back_populates="rule", cascade="all, delete-orphan")


class AlertEvent(Base):
    __tablename__ = "alert_events"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    rule_id = Column(String(36), ForeignKey("alert_rules.id"), nullable=False, index=True)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    severity = Column(String(50), nullable=False)
    metric_value = Column(Float, nullable=False)
    threshold = Column(Float, nullable=False)
    status = Column(String(50), default="firing")  # firing, acknowledged, resolved, suppressed
    fingerprint = Column(String(64), nullable=False, index=True)  # Deduplication hash
    context_json = Column(JSON, default=dict)
    triggered_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)

    rule = relationship("AlertRule", back_populates="events")
    project = relationship("Project")


class IncidentRecord(Base):
    __tablename__ = "incidents"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    environment = Column(String(50), default="production")  # development, staging, production
    severity = Column(String(50), default="high")  # low, medium, high, critical
    status = Column(String(50), default="detected")  # detected, investigating, rca_completed, remediating, resolved, closed
    affected_service = Column(String(100), nullable=False)
    impact_summary = Column(Text, nullable=False)
    lead_alert_id = Column(String(36), nullable=True)
    trace_id = Column(String(64), nullable=True, index=True)
    detected_at = Column(DateTime, default=datetime.utcnow)
    acknowledged_at = Column(DateTime, nullable=True)
    resolved_at = Column(DateTime, nullable=True)

    project = relationship("Project")
    rca = relationship("RCAReport", back_populates="incident", uselist=False, cascade="all, delete-orphan")
    healing_actions = relationship("SelfHealingAction", back_populates="incident")


class RCAReport(Base):
    __tablename__ = "rca_reports"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    incident_id = Column(String(36), ForeignKey("incidents.id"), nullable=False, unique=True)
    probable_root_cause = Column(Text, nullable=False)
    confidence_score = Column(Float, default=0.85)  # 0.0 to 1.0
    supporting_evidence = Column(JSON, default=dict)  # correlated metrics, log traces, deployment sha
    alternative_explanations = Column(JSON, default=list)
    recommended_action = Column(String(255), nullable=False)
    healing_tier = Column(Integer, default=1)  # 1=Auto, 2=Approval Required, 3=Human Only
    risk_assessment = Column(String(100), default="low")
    generated_at = Column(DateTime, default=datetime.utcnow)

    incident = relationship("IncidentRecord", back_populates="rca")


class SelfHealingAction(Base):
    __tablename__ = "self_healing_actions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False, index=True)
    incident_id = Column(String(36), ForeignKey("incidents.id"), nullable=True)
    action_type = Column(String(100), nullable=False)  # restart_container, retry_job, clear_cache, scale_service, rollback_release
    tier = Column(Integer, default=1)  # 1=Auto, 2=Approval Required, 3=Human Only
    status = Column(String(50), default="pending_approval")  # pending_approval, approved, executing, succeeded, failed, rolled_back
    approval_id = Column(String(36), ForeignKey("approval_records.id"), nullable=True)
    parameters = Column(JSON, default=dict)
    execution_log = Column(Text, nullable=True)
    duration_ms = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    executed_at = Column(DateTime, nullable=True)

    project = relationship("Project")
    incident = relationship("IncidentRecord", back_populates="healing_actions")


class SLOConfiguration(Base):
    __tablename__ = "slo_configurations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False, index=True)
    name = Column(String(150), nullable=False)
    target_percentage = Column(Float, default=99.9)  # e.g. 99.9%
    evaluation_window_days = Column(Integer, default=30)
    current_sli = Column(Float, default=99.95)
    error_budget_remaining_percent = Column(Float, default=85.0)
    status = Column(String(50), default="healthy")  # healthy, at_risk, breached
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    project = relationship("Project")


# ---------------------------------------------------------------------------
# Phase 8: Autonomous Maintenance & Continuous Improvement Entities
# ---------------------------------------------------------------------------
class MaintenancePolicy(Base):
    __tablename__ = "maintenance_policies"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False, unique=True)
    schedule = Column(String(50), default="daily")  # daily, weekly, monthly, on_demand
    is_enabled = Column(Boolean, default=True)
    auto_remediate_level1 = Column(Boolean, default=True)
    require_approval_level2 = Column(Boolean, default=True)
    maintenance_window = Column(String(100), default="02:00-04:00 UTC")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    project = relationship("Project")


class MaintenanceTask(Base):
    __tablename__ = "maintenance_tasks"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False, index=True)
    maintenance_type = Column(String(100), nullable=False)  # code_quality, dependency_update, security_remediation, bug_fix, database_maintenance, performance_optimization, technical_debt, documentation, continuous_improvement
    trigger_type = Column(String(50), default="scheduled")  # scheduled, on_demand, security_event, incident_event, dependency_event, performance_event
    schedule = Column(String(50), default="daily")
    priority = Column(String(50), default="medium")  # low, medium, high, critical
    assigned_agents = Column(JSON, default=list)
    status = Column(String(50), default="scheduled")  # scheduled, running, completed, failed, pending_approval
    results = Column(JSON, default=dict)
    logs = Column(Text, nullable=True)
    approval_id = Column(String(36), ForeignKey("approval_records.id"), nullable=True)
    git_branch = Column(String(200), nullable=True)
    pull_request_url = Column(String(500), nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project")
    approval = relationship("ApprovalRecord")


class CodeQualityReport(Base):
    __tablename__ = "code_quality_reports"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False, index=True)
    task_id = Column(String(36), ForeignKey("maintenance_tasks.id"), nullable=True)
    quality_score = Column(Float, default=85.0)  # 0 to 100
    complexity_score = Column(Float, default=12.0)
    duplication_percent = Column(Float, default=2.5)
    maintainability_rating = Column(String(10), default="A")  # A, B, C, D, F
    test_coverage_percent = Column(Float, default=88.5)
    issues_breakdown = Column(JSON, default=dict)
    recommendations = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project")
    task = relationship("MaintenanceTask")


class DependencyVulnerabilityRecord(Base):
    __tablename__ = "dependency_vulnerabilities"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False, index=True)
    package_name = Column(String(150), nullable=False)
    current_version = Column(String(50), nullable=False)
    recommended_version = Column(String(50), nullable=False)
    vulnerability_cve = Column(String(100), nullable=True)
    severity = Column(String(50), default="medium")  # low, medium, high, critical
    ecosystem = Column(String(50), default="python")  # python, npm, docker
    status = Column(String(50), default="open")  # open, remediated, suppressed, pending_approval
    remediation_branch = Column(String(200), nullable=True)
    pr_id = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)

    project = relationship("Project")


class BugReport(Base):
    __tablename__ = "bug_reports"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False, index=True)
    incident_id = Column(String(36), ForeignKey("incidents.id"), nullable=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    reproduction_steps = Column(JSON, default=list)
    root_cause = Column(Text, nullable=True)
    affected_files = Column(JSON, default=list)
    proposed_fix = Column(Text, nullable=True)
    status = Column(String(50), default="detected")  # detected, reproduced, fix_generated, tested, pr_created, resolved
    git_branch = Column(String(200), nullable=True)
    pr_url = Column(String(500), nullable=True)
    test_evidence = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)

    project = relationship("Project")
    incident = relationship("IncidentRecord")


class TechnicalDebtItem(Base):
    __tablename__ = "technical_debt_items"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    category = Column(String(100), default="code_smell")  # architecture, code_smell, deprecated_api, missing_tests, documentation
    severity = Column(String(50), default="medium")  # low, medium, high
    debt_score_impact = Column(Float, default=5.0)
    effort_hours = Column(Float, default=4.0)
    remediation_plan = Column(Text, nullable=False)
    status = Column(String(50), default="backlog")  # backlog, in_progress, resolved
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project")


class ContinuousImprovementProposal(Base):
    __tablename__ = "continuous_improvement_proposals"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    category = Column(String(100), default="reliability")  # performance, reliability, security, cost, architecture
    problem_statement = Column(Text, nullable=False)
    supporting_evidence = Column(JSON, default=dict)
    expected_benefit = Column(Text, nullable=False)
    implementation_complexity = Column(String(50), default="medium")  # low, medium, high
    potential_risk = Column(String(50), default="low")  # low, medium, high
    estimated_cost_usd = Column(Float, default=0.0)
    approval_id = Column(String(36), ForeignKey("approval_records.id"), nullable=True)
    status = Column(String(50), default="proposed")  # proposed, approved, executing, completed, rejected
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project")
    approval = relationship("ApprovalRecord")

