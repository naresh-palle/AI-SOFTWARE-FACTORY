"""
Specialist Agent Registry.
Defines all 97 logical agent roles across Categories A through J.
"""

from typing import Dict, List, Optional
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from factory.core.logger import logger
from factory.models.schema import AgentRegistryRecord


class AgentMetadata(BaseModel):
    role_number: int
    name: str
    role_title: str
    category: str
    description: str
    capabilities: List[str]


# Complete 97 Logical Agent Catalog
AGENT_CATALOG: List[AgentMetadata] = [
    # A. Product and Planning Agents (1-7)
    AgentMetadata(
        role_number=1,
        name="business_analyst",
        role_title="Business Analyst Agent",
        category="Product and Planning",
        description="Analyzes market needs, business goals, user personas, and commercial models.",
        capabilities=["market_analysis", "persona_creation", "monetization_planning"]
    ),
    AgentMetadata(
        role_number=2,
        name="requirement_analysis",
        role_title="Requirement Analysis Agent",
        category="Product and Planning",
        description="Translates raw user requirements into formal functional and non-functional specifications.",
        capabilities=["spec_generation", "user_stories", "acceptance_criteria"]
    ),
    AgentMetadata(
        role_number=3,
        name="research_agent",
        role_title="Research Agent",
        category="Product and Planning",
        description="Investigates domain libraries, protocols, API documentation, and competitor benchmarks.",
        capabilities=["api_research", "library_evaluation", "feasibility_study"]
    ),
    AgentMetadata(
        role_number=4,
        name="product_manager",
        role_title="Product Manager Agent",
        category="Product and Planning",
        description="Prioritizes features, manages scope, establishes MVP milestones, and user journey flows.",
        capabilities=["roadmap_definition", "mvp_scoping", "feature_prioritization"]
    ),
    AgentMetadata(
        role_number=5,
        name="solution_architect",
        role_title="Solution Architect Agent",
        category="Product and Planning",
        description="Designs high-level architecture, module boundaries, communication protocols, and patterns.",
        capabilities=["system_design", "mermaid_diagrams", "protocol_selection"]
    ),
    AgentMetadata(
        role_number=6,
        name="technology_selection",
        role_title="Technology Selection Agent",
        category="Product and Planning",
        description="Dynamically evaluates and selects languages, frameworks, databases, and third-party tools.",
        capabilities=["tech_evaluation", "cost_estimation", "stack_comparison"]
    ),
    AgentMetadata(
        role_number=7,
        name="project_planning",
        role_title="Project Planning Agent",
        category="Product and Planning",
        description="Generates execution graphs, milestone timelines, dependency trees, and resource allocations.",
        capabilities=["wbs_creation", "dependency_mapping", "timeline_estimation"]
    ),

    # B. UI/UX and Frontend Agents (8-14)
    AgentMetadata(
        role_number=8,
        name="ui_ux_designer",
        role_title="UI/UX Designer Agent",
        category="UI/UX and Frontend",
        description="Creates component mockups, user flows, wireframes, and ergonomic interaction patterns.",
        capabilities=["wireframing", "interaction_design", "user_flow_mapping"]
    ),
    AgentMetadata(
        role_number=9,
        name="design_system",
        role_title="Design System Agent",
        category="UI/UX and Frontend",
        description="Defines typography, color palettes, Tailwind tokens, CSS variables, and atomic components.",
        capabilities=["theme_definition", "tailwind_config", "design_tokens"]
    ),
    AgentMetadata(
        role_number=10,
        name="frontend_developer",
        role_title="Frontend Developer Agent",
        category="UI/UX and Frontend",
        description="Implements Next.js, React, TypeScript pages, hooks, state stores, and layout components.",
        capabilities=["nextjs_pages", "react_components", "state_management"]
    ),
    AgentMetadata(
        role_number=11,
        name="responsive_design",
        role_title="Responsive Design Agent",
        category="UI/UX and Frontend",
        description="Ensures pixel-perfect layouts across mobile, tablet, desktop, and ultra-wide viewports.",
        capabilities=["css_media_queries", "flex_grid_tuning", "touch_interactions"]
    ),
    AgentMetadata(
        role_number=12,
        name="accessibility",
        role_title="Accessibility Agent",
        category="UI/UX and Frontend",
        description="Enforces WCAG 2.1 AA compliance, ARIA attributes, semantic HTML, and screen reader readiness.",
        capabilities=["wcag_audit", "aria_attributes", "keyboard_navigation"]
    ),
    AgentMetadata(
        role_number=13,
        name="seo_agent",
        role_title="SEO Agent",
        category="UI/UX and Frontend",
        description="Generates sitemaps, OpenGraph metadata, structured JSON-LD schemas, and robots.txt.",
        capabilities=["metadata_generation", "json_ld_schemas", "sitemap_generation"]
    ),
    AgentMetadata(
        role_number=14,
        name="frontend_performance",
        role_title="Frontend Performance Agent",
        category="UI/UX and Frontend",
        description="Optimizes Core Web Vitals, code-splitting, lazy loading, image formats, and bundle sizes.",
        capabilities=["bundle_analysis", "image_optimization", "caching_headers"]
    ),

    # C. Backend and Mobile Agents (15-23)
    AgentMetadata(
        role_number=15,
        name="backend_architect",
        role_title="Backend Architect Agent",
        category="Backend and Mobile",
        description="Architects REST/GraphQL/gRPC APIs, domain services, clean architecture, and data contracts.",
        capabilities=["domain_modeling", "api_contracts", "clean_architecture"]
    ),
    AgentMetadata(
        role_number=16,
        name="fastapi_developer",
        role_title="FastAPI Developer Agent",
        category="Backend and Mobile",
        description="Develops asynchronous FastAPI endpoints, Pydantic v2 schemas, routers, and middlewares.",
        capabilities=["fastapi_routes", "pydantic_schemas", "async_handlers"]
    ),
    AgentMetadata(
        role_number=17,
        name="api_development",
        role_title="API Development Agent",
        category="Backend and Mobile",
        description="Implements versioned APIs, standardized error responses, pagination, and request validation.",
        capabilities=["versioning", "pagination", "error_handling"]
    ),
    AgentMetadata(
        role_number=18,
        name="microservices",
        role_title="Microservices Agent",
        category="Backend and Mobile",
        description="Structures service boundaries, event-driven messaging, service discovery, and circuit breakers.",
        capabilities=["service_decomposition", "event_bus", "circuit_breaker"]
    ),
    AgentMetadata(
        role_number=19,
        name="android_developer",
        role_title="Android Developer Agent",
        category="Backend and Mobile",
        description="Builds native Android activities, Kotlin coroutines, Jetpack Compose, and manifest files.",
        capabilities=["kotlin_compose", "android_manifest", "gradle_builds"]
    ),
    AgentMetadata(
        role_number=20,
        name="ios_developer",
        role_title="iOS Developer Agent",
        category="Backend and Mobile",
        description="Builds native iOS views, Swift, SwiftUI components, Apple entitlements, and Xcode schemes.",
        capabilities=["swift_ui", "apple_entitlements", "xcode_project"]
    ),
    AgentMetadata(
        role_number=21,
        name="react_native_developer",
        role_title="React Native Developer Agent",
        category="Backend and Mobile",
        description="Builds cross-platform React Native / Expo mobile screens, navigation, and native hooks.",
        capabilities=["expo_app", "react_navigation", "native_modules"]
    ),
    AgentMetadata(
        role_number=22,
        name="websocket_realtime",
        role_title="WebSocket and Realtime Agent",
        category="Backend and Mobile",
        description="Implements bidirectional real-time channels, WebSockets, pub/sub presence, and heartbeats.",
        capabilities=["websocket_endpoints", "connection_manager", "pub_sub"]
    ),
    AgentMetadata(
        role_number=23,
        name="background_jobs",
        role_title="Background Jobs Agent",
        category="Backend and Mobile",
        description="Configures Celery / ARQ / Redis worker queues, scheduled cron tasks, and retry backoffs.",
        capabilities=["celery_tasks", "cron_schedules", "dead_letter_queues"]
    ),

    # D. Database Agents (24-31)
    AgentMetadata(
        role_number=24,
        name="database_architect",
        role_title="Database Architect Agent",
        category="Database",
        description="Designs ER diagrams, normalization/denormalization strategies, indexing, and partitions.",
        capabilities=["er_diagrams", "schema_design", "indexing_strategy"]
    ),
    AgentMetadata(
        role_number=25,
        name="mongodb_agent",
        role_title="MongoDB Agent",
        category="Database",
        description="Implements document schemas, aggregation pipelines, Motor async client, and Mongo indexes.",
        capabilities=["mongo_schemas", "aggregations", "motor_driver"]
    ),
    AgentMetadata(
        role_number=26,
        name="postgresql_agent",
        role_title="PostgreSQL Agent",
        category="Database",
        description="Implements relational DDL, constraints, JSONB columns, asyncpg engine, and performance tuning.",
        capabilities=["postgres_ddl", "constraints", "asyncpg_queries"]
    ),
    AgentMetadata(
        role_number=27,
        name="redis_agent",
        role_title="Redis Agent",
        category="Database",
        description="Configures Redis caching layers, key eviction, pub/sub channels, and rate-limiting counters.",
        capabilities=["cache_keys", "redis_pubsub", "rate_limiters"]
    ),
    AgentMetadata(
        role_number=28,
        name="database_migration",
        role_title="Database Migration Agent",
        category="Database",
        description="Generates and executes Alembic / Flyway migration scripts and rollback plans.",
        capabilities=["alembic_revisions", "schema_upgrades", "downgrade_scripts"]
    ),
    AgentMetadata(
        role_number=29,
        name="database_backup",
        role_title="Database Backup Agent",
        category="Database",
        description="Configures point-in-time recovery, automated snapshot policies, and export scripts.",
        capabilities=["pg_dump_scripts", "s3_backup_sync", "restore_validation"]
    ),
    AgentMetadata(
        role_number=30,
        name="data_engineering",
        role_title="Data Engineering Agent",
        category="Database",
        description="Builds data transformation pipelines, ETL workflows, analytics marts, and exports.",
        capabilities=["etl_pipelines", "data_cleaning", "parquet_exports"]
    ),
    AgentMetadata(
        role_number=31,
        name="file_storage",
        role_title="File Storage Agent",
        category="Database",
        description="Integrates AWS S3, MinIO, presigned upload URLs, multipart uploads, and MIME validation.",
        capabilities=["s3_client", "presigned_urls", "file_validation"]
    ),

    # E. External API Integration Agents (32-47)
    AgentMetadata(
        role_number=32,
        name="api_integration_architect",
        role_title="API Integration Architect",
        category="External API Integration",
        description="Standardizes outbound HTTP clients, retry policies, webhook receivers, and rate limits.",
        capabilities=["api_gateway", "resilience_patterns", "webhook_standards"]
    ),
    AgentMetadata(
        role_number=33,
        name="meta_developer",
        role_title="Meta Developer Agent",
        category="External API Integration",
        description="Coordinates Meta Developer app configurations, scopes, verification, and Graph APIs.",
        capabilities=["meta_app_config", "graph_api_auth", "app_review_readiness"]
    ),
    AgentMetadata(
        role_number=34,
        name="facebook_api",
        role_title="Facebook API Agent",
        category="External API Integration",
        description="Integrates Facebook Login, Page Management APIs, feed publishing, and Webhooks.",
        capabilities=["facebook_login", "page_graph_api", "feed_publishing"]
    ),
    AgentMetadata(
        role_number=35,
        name="instagram_api",
        role_title="Instagram API Agent",
        category="External API Integration",
        description="Integrates Instagram Graph API, media publishing, insights, and comment webhooks.",
        capabilities=["ig_media_publish", "ig_insights", "ig_webhooks"]
    ),
    AgentMetadata(
        role_number=36,
        name="whatsapp_business_api",
        role_title="WhatsApp Business API Agent",
        category="External API Integration",
        description="Configures WhatsApp Business Platform, message templates, Cloud API, and interactive buttons.",
        capabilities=["cloud_api_messages", "template_management", "inbound_webhooks"]
    ),
    AgentMetadata(
        role_number=37,
        name="messenger_api",
        role_title="Messenger API Agent",
        category="External API Integration",
        description="Builds Facebook Messenger chatbots, structured quick-replies, and customer chat widgets.",
        capabilities=["messenger_bot", "quick_replies", "handover_protocol"]
    ),
    AgentMetadata(
        role_number=38,
        name="threads_api",
        role_title="Threads API Agent",
        category="External API Integration",
        description="Integrates official Threads Publishing API, profile insights, and reply management.",
        capabilities=["threads_publishing", "threads_insights", "reply_controls"]
    ),
    AgentMetadata(
        role_number=39,
        name="google_api",
        role_title="Google API Agent",
        category="External API Integration",
        description="Integrates Google Cloud APIs, Drive, Calendar, Sheets, and service account authentication.",
        capabilities=["google_oauth", "google_drive_api", "service_accounts"]
    ),
    AgentMetadata(
        role_number=40,
        name="youtube_api",
        role_title="YouTube API Agent",
        category="External API Integration",
        description="Integrates YouTube Data API v3 for video upload, playlist management, and analytics.",
        capabilities=["youtube_upload", "channel_analytics", "video_search"]
    ),
    AgentMetadata(
        role_number=41,
        name="x_api",
        role_title="X API Agent",
        category="External API Integration",
        description="Integrates X (Twitter) API v2, tweet publishing, user lookups, and webhook streams.",
        capabilities=["tweet_publishing", "oauth2_user_context", "filtered_stream"]
    ),
    AgentMetadata(
        role_number=42,
        name="linkedin_api",
        role_title="LinkedIn API Agent",
        category="External API Integration",
        description="Integrates LinkedIn Community Management APIs, share on LinkedIn, and org posts.",
        capabilities=["linkedin_share", "organization_access", "user_profile_api"]
    ),
    AgentMetadata(
        role_number=43,
        name="tiktok_api",
        role_title="TikTok API Agent",
        category="External API Integration",
        description="Integrates TikTok Content Posting API, Login Kit, and video share integrations.",
        capabilities=["tiktok_login", "video_share_api", "creator_analytics"]
    ),
    AgentMetadata(
        role_number=44,
        name="payment_gateway",
        role_title="Payment Gateway Agent",
        category="External API Integration",
        description="Integrates Stripe / Razorpay checkout sessions, subscriptions, refunds, and webhooks.",
        capabilities=["stripe_checkout", "razorpay_orders", "webhook_signatures"]
    ),
    AgentMetadata(
        role_number=45,
        name="email_integration",
        role_title="Email Integration Agent",
        category="External API Integration",
        description="Configures transactional email via SendGrid, AWS SES, or Resend with HTML templates.",
        capabilities=["sendgrid_client", "ses_client", "html_email_templates"]
    ),
    AgentMetadata(
        role_number=46,
        name="sms_integration",
        role_title="SMS Integration Agent",
        category="External API Integration",
        description="Integrates Twilio / AWS SNS for SMS OTP delivery and transactional notifications.",
        capabilities=["twilio_sms", "otp_dispatch", "sns_mobile"]
    ),
    AgentMetadata(
        role_number=47,
        name="maps_api",
        role_title="Maps API Agent",
        category="External API Integration",
        description="Integrates Google Maps / Mapbox for geocoding, autocomplete, and interactive maps.",
        capabilities=["geocoding", "places_autocomplete", "interactive_map_embed"]
    ),

    # F. Authentication Agents (48-56)
    AgentMetadata(
        role_number=48,
        name="authentication_architect",
        role_title="Authentication Architect",
        category="Authentication",
        description="Designs overall auth architecture, token lifecycle, MFA policies, and session stores.",
        capabilities=["auth_architecture", "jwt_standards", "mfa_design"]
    ),
    AgentMetadata(
        role_number=49,
        name="oauth_integration",
        role_title="OAuth Integration Agent",
        category="Authentication",
        description="Implements standard OAuth 2.0 authorization code flow with PKCE, state, and callbacks.",
        capabilities=["oauth2_pkce", "callback_handler", "token_exchange"]
    ),
    AgentMetadata(
        role_number=50,
        name="google_login",
        role_title="Google Login Agent",
        category="Authentication",
        description="Implements Google One-Tap, OAuth client configuration, and ID token verification.",
        capabilities=["google_id_tokens", "google_one_tap", "profile_sync"]
    ),
    AgentMetadata(
        role_number=51,
        name="facebook_login",
        role_title="Facebook Login Agent",
        category="Authentication",
        description="Implements Facebook Login SDK, Graph OAuth code exchange, and user profile sync.",
        capabilities=["fb_oauth", "token_inspection", "profile_mapping"]
    ),
    AgentMetadata(
        role_number=52,
        name="otp_verification",
        role_title="OTP Verification Agent",
        category="Authentication",
        description="Generates, stores, hashes, and validates time-limited 6-digit OTPs via Redis.",
        capabilities=["otp_generation", "redis_ttl_verification", "rate_limiting"]
    ),
    AgentMetadata(
        role_number=53,
        name="user_management",
        role_title="User Management Agent",
        category="Authentication",
        description="Builds user registration, profile updates, account deletion (GDPR), and password reset.",
        capabilities=["user_crud", "password_reset", "gdpr_deletion"]
    ),
    AgentMetadata(
        role_number=54,
        name="rbac_agent",
        role_title="RBAC Agent",
        category="Authentication",
        description="Implements Role-Based Access Control, permission matrix, route guards, and decorators.",
        capabilities=["role_matrix", "permission_checks", "route_guards"]
    ),
    AgentMetadata(
        role_number=55,
        name="session_management",
        role_title="Session Management Agent",
        category="Authentication",
        description="Configures secure HttpOnly cookie sessions, Redis session stores, and device tracking.",
        capabilities=["httponly_cookies", "session_invalidation", "device_tracking"]
    ),
    AgentMetadata(
        role_number=56,
        name="token_management",
        role_title="Token Management Agent",
        category="Authentication",
        description="Handles JWT minting, asymmetric RS256/Ed25519 signatures, refresh tokens, and blacklists.",
        capabilities=["jwt_minting", "refresh_rotation", "token_revocation"]
    ),

    # G. Security Agents (57-65)
    AgentMetadata(
        role_number=57,
        name="security_architect",
        role_title="Security Architect",
        category="Security",
        description="Establishes zero-trust posture, threat models, encryption standards, and defense-in-depth.",
        capabilities=["threat_modeling", "zero_trust", "security_checklists"]
    ),
    AgentMetadata(
        role_number=58,
        name="application_security",
        role_title="Application Security Agent",
        category="Security",
        description="Protects against OWASP Top 10: XSS, CSRF, SQLi, SSRF, IDOR, and input sanitization.",
        capabilities=["owasp_protection", "input_sanitization", "csrf_tokens"]
    ),
    AgentMetadata(
        role_number=59,
        name="api_security",
        role_title="API Security Agent",
        category="Security",
        description="Implements API rate-limiting, CORS policies, secure headers (HSTS, CSP), and payload limits.",
        capabilities=["rate_limiting", "secure_headers", "cors_configuration"]
    ),
    AgentMetadata(
        role_number=60,
        name="oauth_security",
        role_title="OAuth Security Agent",
        category="Security",
        description="Audits OAuth redirect URI validation, state parameter CSRF defense, and scope minimization.",
        capabilities=["redirect_uri_validation", "state_verification", "scope_audit"]
    ),
    AgentMetadata(
        role_number=61,
        name="secrets_management",
        role_title="Secrets Management Agent",
        category="Security",
        description="Enforces secrets encryption at rest, environment variable isolation, and prevents secret leaks.",
        capabilities=["fernet_encryption", "secret_scanning", "vault_integration"]
    ),
    AgentMetadata(
        role_number=62,
        name="vulnerability_scanning",
        role_title="Vulnerability Scanning Agent",
        category="Security",
        description="Executes dependency vulnerability audits (pip-audit, npm audit, Trivy scanners).",
        capabilities=["dependency_audit", "trivy_scanning", "cve_analysis"]
    ),
    AgentMetadata(
        role_number=63,
        name="penetration_testing",
        role_title="Penetration Testing Agent",
        category="Security",
        description="Performs automated DAST / mock penetration tests against endpoints and auth mechanisms.",
        capabilities=["dast_testing", "auth_fuzzing", "header_inspection"]
    ),
    AgentMetadata(
        role_number=64,
        name="data_privacy",
        role_title="Data Privacy Agent",
        category="Security",
        description="Ensures GDPR / CCPA compliance, PII masking, data retention policies, and export endpoints.",
        capabilities=["pii_masking", "gdpr_compliance", "privacy_policy_specs"]
    ),
    AgentMetadata(
        role_number=65,
        name="audit_logging",
        role_title="Audit Logging Agent",
        category="Security",
        description="Captures immutable structured audit trails of all sensitive user, admin, and agent actions.",
        capabilities=["audit_trail", "tamper_evident_logs", "compliance_exports"]
    ),

    # H. DevOps and Cloud Agents (66-79)
    AgentMetadata(
        role_number=66,
        name="cloud_architect",
        role_title="Cloud Architect",
        category="DevOps and Cloud",
        description="Architects cloud topology on AWS, multi-AZ high availability, and network VPC design.",
        capabilities=["cloud_topology", "vpc_design", "cost_effective_infra"]
    ),
    AgentMetadata(
        role_number=67,
        name="aws_infrastructure",
        role_title="AWS Infrastructure Agent",
        category="DevOps and Cloud",
        description="Configures AWS ECS/EKS, RDS, S3, CloudFront, IAM roles, and Security Groups.",
        capabilities=["aws_iam", "ecs_task_definitions", "s3_buckets"]
    ),
    AgentMetadata(
        role_number=68,
        name="terraform_agent",
        role_title="Terraform Agent",
        category="DevOps and Cloud",
        description="Writes modular, declarative Terraform scripts (HCL) with remote state and locking.",
        capabilities=["terraform_modules", "hcl_generation", "state_locking"]
    ),
    AgentMetadata(
        role_number=69,
        name="docker_agent",
        role_title="Docker Agent",
        category="DevOps and Cloud",
        description="Writes production multi-stage Dockerfiles and optimized docker-compose configurations.",
        capabilities=["dockerfile_generation", "compose_files", "container_optimization"]
    ),
    AgentMetadata(
        role_number=70,
        name="kubernetes_agent",
        role_title="Kubernetes Agent",
        category="DevOps and Cloud",
        description="Creates Kubernetes Deployments, Services, Ingress, ConfigMaps, and Secrets manifests.",
        capabilities=["k8s_manifests", "ingress_rules", "hpa_scaling"]
    ),
    AgentMetadata(
        role_number=71,
        name="helm_agent",
        role_title="Helm Agent",
        category="DevOps and Cloud",
        description="Packages application manifests into reusable Helm charts with templated values.yaml.",
        capabilities=["helm_charts", "values_templating", "chart_packaging"]
    ),
    AgentMetadata(
        role_number=72,
        name="jenkins_agent",
        role_title="Jenkins Agent",
        category="DevOps and Cloud",
        description="Generates Jenkinsfiles, declarative multi-branch pipelines, and test reporting stages.",
        capabilities=["jenkinsfile_generation", "pipeline_stages", "build_artifacts"]
    ),
    AgentMetadata(
        role_number=73,
        name="github_integration",
        role_title="GitHub Integration Agent",
        category="DevOps and Cloud",
        description="Automates GitHub repo creation, branch rules, PR generation, and GitHub Actions workflows.",
        capabilities=["github_repo_init", "actions_workflows", "pr_automation"]
    ),
    AgentMetadata(
        role_number=74,
        name="argocd_agent",
        role_title="ArgoCD Agent",
        category="DevOps and Cloud",
        description="Configures GitOps synchronization, Application CRDs, and progressive delivery via ArgoCD.",
        capabilities=["argocd_applications", "gitops_sync", "automated_rollback"]
    ),
    AgentMetadata(
        role_number=75,
        name="dns_ssl",
        role_title="DNS and SSL Agent",
        category="DevOps and Cloud",
        description="Configures Let's Encrypt / Certbot, ACM SSL certificates, Route53, and HTTPS redirection.",
        capabilities=["ssl_certificates", "dns_records", "https_enforcement"]
    ),
    AgentMetadata(
        role_number=76,
        name="monitoring_agent",
        role_title="Monitoring Agent",
        category="DevOps and Cloud",
        description="Configures Prometheus metrics exporter, Grafana dashboards, and uptime alerts.",
        capabilities=["prometheus_metrics", "grafana_dashboards", "alert_rules"]
    ),
    AgentMetadata(
        role_number=77,
        name="logging_agent",
        role_title="Logging Agent",
        category="DevOps and Cloud",
        description="Configures centralized structured logging (JSON format), log aggregation, and filters.",
        capabilities=["json_logging", "log_aggregation", "log_correlation"]
    ),
    AgentMetadata(
        role_number=78,
        name="disaster_recovery",
        role_title="Disaster Recovery Agent",
        category="DevOps and Cloud",
        description="Prepares disaster recovery runbooks, automated failover plans, and RPO/RTO objectives.",
        capabilities=["dr_runbooks", "rpo_rto_specs", "failover_procedures"]
    ),
    AgentMetadata(
        role_number=79,
        name="finops_agent",
        role_title="FinOps Agent",
        category="DevOps and Cloud",
        description="Tracks infrastructure resource allocations, estimates AWS costs, and optimizes compute sizing.",
        capabilities=["cloud_cost_modeling", "resource_rightsizing", "budget_alerts"]
    ),

    # I. Testing Agents (80-91)
    AgentMetadata(
        role_number=80,
        name="qa_architect",
        role_title="QA Architect",
        category="Testing",
        description="Designs master QA strategy, test matrices, test data generation, and pass/fail gates.",
        capabilities=["qa_strategy", "test_matrix", "quality_gates"]
    ),
    AgentMetadata(
        role_number=81,
        name="unit_testing",
        role_title="Unit Testing Agent",
        category="Testing",
        description="Writes automated Pytest / Jest unit tests with high branch coverage and mocking.",
        capabilities=["pytest_generation", "jest_tests", "mock_fixtures"]
    ),
    AgentMetadata(
        role_number=82,
        name="api_testing",
        role_title="API Testing Agent",
        category="Testing",
        description="Writes and runs automated REST API tests verifying status codes, schemas, and headers.",
        capabilities=["api_functional_tests", "schema_validation", "http_assertion"]
    ),
    AgentMetadata(
        role_number=83,
        name="integration_testing",
        role_title="Integration Testing Agent",
        category="Testing",
        description="Executes cross-service integration tests against live DB containers and queues.",
        capabilities=["db_integration_tests", "end_to_end_flow", "testcontainers"]
    ),
    AgentMetadata(
        role_number=84,
        name="ui_automation",
        role_title="UI Automation Agent",
        category="Testing",
        description="Builds Playwright / Cypress browser automation scripts for UI and end-to-end user flows.",
        capabilities=["playwright_scripts", "e2e_browser_tests", "screenshot_diffing"]
    ),
    AgentMetadata(
        role_number=85,
        name="mobile_testing",
        role_title="Mobile Testing Agent",
        category="Testing",
        description="Configures Appium / Maestro test suites for Android and iOS mobile application flows.",
        capabilities=["appium_tests", "maestro_flows", "mobile_assertions"]
    ),
    AgentMetadata(
        role_number=86,
        name="performance_testing",
        role_title="Performance Testing Agent",
        category="Testing",
        description="Configures Locust / k6 load and stress tests, identifying latency bottlenecks and TPS limits.",
        capabilities=["locust_load_tests", "k6_scripts", "tps_measurement"]
    ),
    AgentMetadata(
        role_number=87,
        name="security_testing",
        role_title="Security Testing Agent",
        category="Testing",
        description="Executes automated SAST scans, dependency vulnerability scans, and security regressions.",
        capabilities=["sast_scans", "security_assertions", "credential_leak_checks"]
    ),
    AgentMetadata(
        role_number=88,
        name="regression_testing",
        role_title="Regression Testing Agent",
        category="Testing",
        description="Ensures existing test cases are preserved and pass on every incremental commit.",
        capabilities=["regression_suite", "baseline_comparisons", "fail_on_drift"]
    ),
    AgentMetadata(
        role_number=89,
        name="bug_fixing",
        role_title="Bug Fixing Agent",
        category="Testing",
        description="Analyzes stack traces, reproduces errors, generates targeted patches, and verifies fixes.",
        capabilities=["stacktrace_analysis", "patch_generation", "fix_verification"]
    ),
    AgentMetadata(
        role_number=90,
        name="code_review",
        role_title="Code Review Agent",
        category="Testing",
        description="Performs automated code reviews checking PEP8, Clean Architecture, and maintainability.",
        capabilities=["ast_code_review", "linting_checks", "pr_comments"]
    ),
    AgentMetadata(
        role_number=91,
        name="release_validation",
        role_title="Release Validation Agent",
        category="Testing",
        description="Performs final sanity checklist verification before green-lighting production deployments.",
        capabilities=["release_checklist", "smoke_tests", "deployment_gate"]
    ),

    # J. Maintenance Agents (92-97)
    AgentMetadata(
        role_number=92,
        name="technical_documentation",
        role_title="Technical Documentation Agent",
        category="Maintenance",
        description="Generates README.md, architecture docs, development guides, and deployment manuals.",
        capabilities=["readme_generation", "architecture_docs", "runbook_generation"]
    ),
    AgentMetadata(
        role_number=93,
        name="api_documentation",
        role_title="API Documentation Agent",
        category="Maintenance",
        description="Generates OpenAPI 3.1 JSON/YAML, Swagger UI specs, and Postman collection files.",
        capabilities=["openapi_specs", "swagger_docs", "postman_collections"]
    ),
    AgentMetadata(
        role_number=94,
        name="production_support",
        role_title="Production Support Agent",
        category="Maintenance",
        description="Analyzes runtime error logs, correlates issues, and drafts initial triage recommendations.",
        capabilities=["log_triage", "error_correlation", "support_tickets"]
    ),
    AgentMetadata(
        role_number=95,
        name="incident_management",
        role_title="Incident Management Agent",
        category="Maintenance",
        description="Structures post-mortems, incident timelines, root-cause analyses, and action items.",
        capabilities=["rca_generation", "incident_timeline", "post_mortem_reports"]
    ),
    AgentMetadata(
        role_number=96,
        name="dependency_update",
        role_title="Dependency Update Agent",
        category="Maintenance",
        description="Checks for outdated packages, security patches, and generates automated upgrade PRs.",
        capabilities=["outdated_package_scan", "upgrade_plans", "breaking_change_checks"]
    ),
    AgentMetadata(
        role_number=97,
        name="application_maintenance",
        role_title="Application Maintenance Agent",
        category="Maintenance",
        description="Coordinates periodic maintenance windows, db vacuums, log pruning, and health audits.",
        capabilities=["maintenance_routines", "health_audits", "housekeeping_jobs"]
    ),
]


class AgentRegistry:
    """Manages the agent catalog and DB synchronization."""

    @classmethod
    def get_all_agents(cls) -> List[AgentMetadata]:
        return AGENT_CATALOG

    @classmethod
    def get_by_role_number(cls, role_number: int) -> Optional[AgentMetadata]:
        for agent in AGENT_CATALOG:
            if agent.role_number == role_number:
                return agent
        return None

    @classmethod
    def get_by_name(cls, name: str) -> Optional[AgentMetadata]:
        for agent in AGENT_CATALOG:
            if agent.name == name or agent.role_title.lower() == name.lower():
                return agent
        return None

    @classmethod
    def get_by_category(cls, category: str) -> List[AgentMetadata]:
        return [a for a in AGENT_CATALOG if category.lower() in a.category.lower()]

    @classmethod
    async def sync_with_db(cls, session: AsyncSession) -> int:
        """Populate database with all 97 agents if not present."""
        created_count = 0
        for agent in AGENT_CATALOG:
            stmt = select(AgentRegistryRecord).where(AgentRegistryRecord.role_number == agent.role_number)
            result = await session.execute(stmt)
            existing = result.scalar_one_or_none()
            if not existing:
                record = AgentRegistryRecord(
                    role_number=agent.role_number,
                    name=agent.name,
                    role_title=agent.role_title,
                    category=agent.category,
                    description=agent.description,
                    capabilities=agent.capabilities,
                    is_active=True
                )
                session.add(record)
                created_count += 1
        await session.flush()
        if created_count > 0:
            logger.info(f"Synchronized {created_count} agents to database registry.")
        return created_count
