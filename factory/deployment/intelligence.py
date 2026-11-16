"""
Deployment Intelligence Engine.
Analyzes project workspace, requirement constraints, and technology stack
to dynamically select the optimal deployment architecture without assuming Kubernetes for everything.
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class DeploymentProfile(BaseModel):
    app_type: str  # static_website, nextjs, react_spa, fastapi, nodejs, java, microservices, kubernetes, android, ios
    frontend_framework: Optional[str] = None
    backend_framework: Optional[str] = None
    primary_language: str = "python"
    database_required: Optional[str] = None
    cache_required: Optional[str] = None
    container_required: bool = True
    target_architecture: str = "aws_ecs_fargate"  # aws_s3_cloudfront, aws_ecs_fargate, kubernetes, mobile_release
    recommended_strategy: str = "rolling"  # rolling, blue_green, canary
    scaling_tier: str = "standard"  # lightweight, standard, high_scale
    estimated_monthly_cost_usd: float = 35.0
    env_vars_required: List[str] = Field(default_factory=list)
    secrets_required: List[str] = Field(default_factory=list)
    rationale: str = ""


class DeploymentIntelligenceEngine:
    """Inspects project structure and requirements to compute deployment profile."""

    @staticmethod
    def analyze_project(
        project_dir: Path,
        requirement_text: str = "",
        platform_target: str = "fullstack",
    ) -> DeploymentProfile:
        req_lower = requirement_text.lower()
        has_package_json = (project_dir / "package.json").exists() or (project_dir / "frontend" / "package.json").exists()
        has_requirements = (project_dir / "requirements.txt").exists() or (project_dir / "backend" / "requirements.txt").exists()
        has_dockerfile = (project_dir / "Dockerfile").exists()
        has_android = (project_dir / "android").exists() or "android" in req_lower
        has_ios = (project_dir / "ios").exists() or "ios" in req_lower

        # 1. Detect Mobile Application Target
        if platform_target in ["android", "ios", "mobile"] or has_android or has_ios:
            app_type = "android" if has_android and not has_ios else ("ios" if has_ios and not has_android else "mobile_cross_platform")
            return DeploymentProfile(
                app_type=app_type,
                primary_language="kotlin/swift",
                container_required=False,
                target_architecture="mobile_release",
                recommended_strategy="rolling",
                scaling_tier="lightweight",
                estimated_monthly_cost_usd=25.0,  # Developer account amortized
                env_vars_required=["APP_ENV", "API_BASE_URL"],
                secrets_required=["MOBILE_SIGNING_KEYSTORE", "PROVISIONING_PROFILE"],
                rationale="Mobile application detected. Selected Mobile Release pipeline generating signed .aab and .ipa store artifacts.",
            )

        # 2. Detect High-scale Microservices / Explicit Kubernetes
        if "kubernetes" in req_lower or "k8s" in req_lower or "microservice" in req_lower:
            return DeploymentProfile(
                app_type="kubernetes_microservices",
                frontend_framework="Next.js" if has_package_json else None,
                backend_framework="FastAPI" if has_requirements else "Node.js",
                primary_language="python" if has_requirements else "typescript",
                database_required="PostgreSQL",
                cache_required="Redis",
                container_required=True,
                target_architecture="kubernetes",
                recommended_strategy="canary",
                scaling_tier="high_scale",
                estimated_monthly_cost_usd=120.0,
                env_vars_required=["ENVIRONMENT", "DATABASE_URL", "REDIS_URL"],
                secrets_required=["DB_PASSWORD", "SECRET_KEY"],
                rationale="High-scale distributed workload requested. Kubernetes cluster with Helm charts, HPA, and Canary deployment selected.",
            )

        # 3. Detect Pure Static / React SPA
        if not has_requirements and has_package_json and ("static" in req_lower or "landing" in req_lower):
            return DeploymentProfile(
                app_type="static_website",
                frontend_framework="React SPA",
                primary_language="typescript",
                database_required=None,
                container_required=False,
                target_architecture="aws_s3_cloudfront",
                recommended_strategy="blue_green",
                scaling_tier="lightweight",
                estimated_monthly_cost_usd=5.0,
                env_vars_required=["NEXT_PUBLIC_API_URL"],
                secrets_required=[],
                rationale="Static frontend SPA detected. Serverless S3 hosting with CloudFront global CDN distribution selected for maximum performance and minimal cost.",
            )

        # 4. Standard Full-Stack Web / API (Default: AWS ECS/Fargate)
        return DeploymentProfile(
            app_type="fullstack_web_api",
            frontend_framework="Next.js" if has_package_json else "HTML5/Tailwind",
            backend_framework="FastAPI" if has_requirements else "FastAPI",
            primary_language="python",
            database_required="PostgreSQL",
            cache_required="Redis" if "cache" in req_lower or "session" in req_lower else None,
            container_required=True,
            target_architecture="aws_ecs_fargate",
            recommended_strategy="rolling",
            scaling_tier="standard",
            estimated_monthly_cost_usd=35.0,
            env_vars_required=["ENVIRONMENT", "DATABASE_URL", "APP_NAME"],
            secrets_required=["DATABASE_PASSWORD", "SECRET_KEY", "ENCRYPTION_KEY"],
            rationale="Full-stack containerized web application detected. AWS ECS/Fargate serverless containers selected for isolated reliability and automated zero-downtime rolling updates.",
        )
