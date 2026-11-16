"""
Intelligent Technology Selection and Dynamic Agent Assignment Engine.
Evaluates requirements, compares tech options, estimates costs, and selects
the exact required subset of specialist agents.
"""

import re
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from factory.agents.registry import AGENT_CATALOG, AgentMetadata
from factory.core.logger import logger
from factory.llm.provider import BaseLLMProvider, get_llm_provider


class TechnologyDecision(BaseModel):
    frontend: str
    backend: str
    mobile: Optional[str] = None
    database: str
    cache: Optional[str] = None
    payments: Optional[str] = None
    auth: str
    cloud_infra: str
    ci_cd: str
    rationale: Dict[str, str] = Field(default_factory=dict)


class ProjectPlan(BaseModel):
    project_title: str
    platform_targets: List[str]
    technology_stack: TechnologyDecision
    selected_agent_roles: List[str]
    selected_agent_numbers: List[int]
    api_dependencies: List[str] = Field(default_factory=list)
    licensing_requirements: List[str] = Field(default_factory=list)
    approval_checkpoints: List[str] = Field(default_factory=list)
    estimated_monthly_cost_usd: float = 0.0
    mermaid_architecture: str = ""


def contains_term(text: str, term: str) -> bool:
    """Match a keyword on word boundaries so 'application' does not match 'app'."""
    return re.search(rf"\b{re.escape(term.lower())}\b", text) is not None


def contains_any(text: str, terms: List[str]) -> bool:
    return any(contains_term(text, term) for term in terms)


class DynamicAgentSelector:
    """Evaluates software requirements and dynamically determines tech stack & agent assignments."""

    def __init__(self, llm_provider: Optional[BaseLLMProvider] = None):
        self.llm = llm_provider or get_llm_provider()

    async def analyze_and_select(
        self,
        requirement_text: str,
        user_platform_target: Optional[str] = None,
    ) -> ProjectPlan:
        logger.info("DynamicAgentSelector: Analyzing requirement text...")
        req_lower = requirement_text.lower()

        # 1. Platform Detection
        platforms = []
        if user_platform_target and user_platform_target not in ("auto", "fullstack", "combined"):
            platforms.append(user_platform_target)
        else:
            has_mobile = contains_any(req_lower, ["mobile", "android", "ios", "react native", "phone", "app"])
            has_web = contains_any(req_lower, ["web", "website", "dashboard", "portal", "store", "commerce", "saas", "frontend"]) or not has_mobile
            if has_web:
                platforms.append("website")
            if has_mobile or contains_term(req_lower, "android"):
                platforms.append("mobile_android")
            if has_mobile or contains_term(req_lower, "ios") or contains_term(req_lower, "iphone"):
                platforms.append("mobile_ios")

        # 2. Technology Selection Analysis
        # Frontend selection
        frontend = "Next.js 14 + React + TypeScript + Tailwind CSS"
        frontend_rationale = "Next.js provides Server-Side Rendering, SEO readiness, and robust TypeScript ergonomics."

        # Mobile selection
        mobile = None
        mobile_rationale = ""
        if "mobile_android" in platforms or "mobile_ios" in platforms:
            mobile = "React Native + Expo"
            mobile_rationale = "Cross-platform mobile codebase for unified Android and iOS development with native bridges."

        # Backend selection
        backend = "FastAPI + Python 3.10"
        backend_rationale = "High-performance asynchronous Python backend with automatic OpenAPI schema generation."

        # Database selection
        is_relational = contains_any(
            req_lower,
            [
                "relational",
                "financial",
                "payment",
                "e-commerce",
                "ecommerce",
                "order",
                "invoice",
                "bank",
                "sql",
                "acid",
                "postgresql",
                "postgres",
                "employee",
                "employees",
                "staff",
                "payroll",
            ],
        )
        if is_relational:
            database = "PostgreSQL"
            db_rationale = "ACID-compliant relational integrity with JSONB capability for complex transactions and catalog items."
        else:
            database = "MongoDB"
            db_rationale = "Flexible document schema for rapid iteration on unstructured or evolving content."

        # Cache selection
        needs_cache = contains_any(req_lower, ["cache", "session", "high traffic", "realtime", "chat", "streaming", "scale", "redis"])
        cache = "Redis" if needs_cache or is_relational else None
        cache_rationale = "In-memory caching, rate-limiting counters, and pub/sub message brokering." if cache else "Direct database queries sufficient for initial workload."

        # Payments
        payments = None
        needs_payment = contains_any(req_lower, ["pay", "payment", "checkout", "subscription", "stripe", "razorpay", "billing", "cart"])
        if needs_payment:
            payments = "Stripe & Razorpay Multi-Gateway"
            payments_rationale = "Global credit card support via Stripe plus regional UPI/Netbanking via Razorpay."
        else:
            payments_rationale = "No e-commerce or monetized transactions detected."

        # Authentication
        auth = "OAuth 2.0 (Google & Meta) + JWT Secure HttpOnly Sessions"
        auth_rationale = "Zero-password onboarding with tenant isolation and cryptographic JWT session validation."

        # Cloud & CI/CD
        cloud_infra = "AWS (ECS / EKS, RDS, S3, CloudFront)"
        ci_cd = "GitHub Actions with Automated Lint, Test & Security Scanning"

        tech_decision = TechnologyDecision(
            frontend=frontend,
            backend=backend,
            mobile=mobile,
            database=database,
            cache=cache,
            payments=payments,
            auth=auth,
            cloud_infra=cloud_infra,
            ci_cd=ci_cd,
            rationale={
                "frontend": frontend_rationale,
                "backend": backend_rationale,
                "mobile": mobile_rationale,
                "database": db_rationale,
                "cache": cache_rationale,
                "payments": payments_rationale,
                "auth": auth_rationale,
            }
        )

        # 3. Dynamic Specialist Agent Selection (Exact subset required)
        selected_numbers: List[int] = [
            # Mandatory Core Planning & Architecture
            1,   # Business Analyst
            2,   # Requirement Analysis
            5,   # Solution Architect
            6,   # Technology Selection
            7,   # Project Planning
            # Core Backend
            15,  # Backend Architect
            16,  # FastAPI Developer
            17,  # API Development
            # Core Database
            24,  # Database Architect
            # Core Auth & Security
            48,  # Authentication Architect
            49,  # OAuth Integration
            53,  # User Management
            56,  # Token Management
            57,  # Security Architect
            58,  # Application Security
            59,  # API Security
            61,  # Secrets Management
            # Core DevOps & Repo
            66,  # Cloud Architect
            69,  # Docker Agent
            73,  # GitHub Integration
            # Core QA & Testing
            80,  # QA Architect
            81,  # Unit Testing
            82,  # API Testing
            88,  # Regression Testing
            90,  # Code Review
            92,  # Technical Documentation
        ]

        # Frontend Agents
        if "website" in platforms:
            selected_numbers.extend([8, 9, 10, 11, 12, 13, 84])  # UI/UX, Design System, Frontend Dev, Responsive, A11y, SEO, UI Automation

        # Mobile Agents
        if "mobile_android" in platforms or "mobile_ios" in platforms:
            selected_numbers.extend([21, 85])  # React Native Dev, Mobile Testing
            if "mobile_android" in platforms:
                selected_numbers.append(19)  # Android Dev
            if "mobile_ios" in platforms:
                selected_numbers.append(20)  # iOS Dev

        # Database Agents
        if database == "PostgreSQL":
            selected_numbers.extend([26, 28])  # PostgreSQL Agent, Database Migration
        elif database == "MongoDB":
            selected_numbers.append(25)  # MongoDB Agent

        # Cache & Background
        if cache == "Redis":
            selected_numbers.extend([27, 23])  # Redis Agent, Background Jobs

        # Payments
        if payments:
            selected_numbers.append(44)  # Payment Gateway Agent
        if contains_any(req_lower, ["employee", "employees", "staff", "rbac", "role", "roles"]):
            selected_numbers.append(54)  # RBAC Agent
        if contains_any(req_lower, ["facebook", "oauth"]):
            selected_numbers.append(51)  # Facebook Login Agent

        # Social & External APIs
        api_deps: List[str] = []
        if contains_any(req_lower, ["meta", "facebook", "instagram", "whatsapp"]):
            selected_numbers.extend([33, 34, 35, 36])
            api_deps.append("Meta Graph API (Facebook, Instagram, WhatsApp)")
        if contains_term(req_lower, "youtube"):
            selected_numbers.append(40)
            api_deps.append("YouTube Data API v3")
        if contains_any(req_lower, ["twitter", "x api"]):
            selected_numbers.append(41)
            api_deps.append("X API v2")
        if contains_term(req_lower, "google"):
            selected_numbers.extend([39, 50])
            api_deps.append("Google APIs & Google OAuth")
        if contains_any(req_lower, ["email", "mail", "notification"]):
            selected_numbers.append(45)
            api_deps.append("SendGrid / AWS SES Email API")

        # Deduplicate & sort selected numbers
        selected_numbers = sorted(list(set(selected_numbers)))
        agent_role_titles = []
        for num in selected_numbers:
            for ag in AGENT_CATALOG:
                if ag.role_number == num:
                    agent_role_titles.append(ag.role_title)
                    break

        # Checkpoints & Costs
        checkpoints = ["Project Architecture Sign-off"]
        if payments:
            checkpoints.append("Payment Gateway Credentials & Webhook Activation")
        if api_deps:
            checkpoints.append("Third-party OAuth App Creation & Review Approval")
        checkpoints.append("Production Deployment Gate Approval")

        # Cost estimation
        base_cost = 25.0
        if "PostgreSQL" in database:
            base_cost += 15.0
        if cache:
            base_cost += 10.0
        if "mobile_android" in platforms or "mobile_ios" in platforms:
            base_cost += 10.0

        # Mermaid Diagram
        mermaid = (
            "graph TD\n"
            "  ClientWeb[Next.js 14 Web Frontend] --> APIGateway[FastAPI Async API Gateway]\n"
        )
        if mobile:
            mermaid += "  ClientMobile[React Native Mobile App] --> APIGateway\n"
        mermaid += (
            f"  APIGateway --> AuthSvc[Authentication & RBAC ({auth})]\n"
            f"  APIGateway --> CoreDB[({database} Database)]\n"
        )
        if cache:
            mermaid += f"  APIGateway --> CacheSvc[({cache} Cache & Bus)]\n"
        if payments:
            mermaid += f"  APIGateway --> PaySvc[{payments}]\n"

        return ProjectPlan(
            project_title=f"Autonomous Project: {requirement_text[:40]}...",
            platform_targets=platforms,
            technology_stack=tech_decision,
            selected_agent_roles=agent_role_titles,
            selected_agent_numbers=selected_numbers,
            api_dependencies=api_deps,
            licensing_requirements=["MIT Open Source Core Libraries", "Commercial Platform SDK Terms"],
            approval_checkpoints=checkpoints,
            estimated_monthly_cost_usd=base_cost,
            mermaid_architecture=mermaid
        )
