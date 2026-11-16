# Autonomous AI Software Development Factory

[![CI / Regression Test Suite](https://img.shields.io/badge/Tests-115%20Passed-brightgreen.svg)](tests/)
[![Commercial Launch Status](https://img.shields.io/badge/Commercial%20Launch-SUCCESS-blue.svg)](phase11_controlled_production_launch_report.md)
[![Release Version](https://img.shields.io/badge/Release-v1.0.0--prod-indigo.svg)](https://github.com/naresh-palle/AI-SOFTWARE-FACTORY/releases/tag/v1.0.0-prod)
[![Python Version](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Frontend-Next.js%2014-black.svg)](https://nextjs.org/)
[![License](https://img.shields.io/badge/License-Proprietary-red.svg)](#license)

An enterprise-grade, autonomous, cloud-native **AI Software Development Factory** that converts single natural-language software requirements into fully designed, implemented, tested, containerized, deployed, monitored, and autonomously maintained production applications.

---

## Table of Contents

- [Key Capabilities](#key-capabilities)
- [Architecture & 97-Agent Registry](#architecture--97-agent-registry)
- [System Requirements](#system-requirements)
- [Quick Start](#quick-start)
  - [1. One-Click Automated Startup](#1-one-click-automated-startup)
  - [2. Docker Compose Startup](#2-docker-compose-startup)
  - [3. Manual Setup (Backend + Frontend)](#3-manual-setup-backend--frontend)
- [How to Use](#how-to-use)
  - [A. Web Management Dashboard (UI)](#a-web-management-dashboard-ui)
  - [B. Command Line Interface (CLI)](#b-command-line-interface-cli)
  - [C. REST API Interactive Docs](#c-rest-api-interactive-docs)
  - [D. Python SDK / Programmatic API](#d-python-sdk--programmatic-api)
- [Development Lifecycle & 23 Stages](#development-lifecycle--23-stages)
- [Cloud Execution Workers & Deployment](#cloud-execution-workers--deployment)
- [AIOps, Self-Healing & Maintenance](#aiops-self-healing--maintenance)
- [Multi-Tenant SaaS, FinOps & Billing](#multi-tenant-saas-finops--billing)
- [Testing & Quality Verification](#testing--quality-verification)
- [Configuration & Environment Variables](#configuration--environment-variables)
- [License & Support](#license--support)

---

## Key Capabilities

1. **Autonomous Code Generation Engine**:
   - Accepts one natural-language requirement (e.g. *"Build a real-time cryptocurrency portfolio tracker with price alerts and Stripe subscriptions"*).
   - Dynamically selects optimal tech stack (React/Next.js, FastAPI/Node, PostgreSQL, Redis, TailwindCSS).
   - Scaffold complete frontend, backend, database models, Docker packaging, and automated test suites.
2. **Master Orchestrator with 97 Specialist Agents**:
   - Catalog of 97 discrete specialist roles (Architects, Frontend/Backend engineers, Mobile devs, QA, SecOps, FinOps, SRE).
   - Dynamic Agent Selection Engine based on semantic analysis and complexity scoring.
   - Dual-loop regression safety: strictly forbids code changes that break existing tests.
3. **Cloud Worker & Workflow Engine**:
   - Autonomous background task execution via Celery, Redis, and containerized cloud workers (Docker/AWS Fargate).
   - Executes even when local IDE or client machine is offline or closed.
4. **Autonomous Release & Deployment Engine**:
   - Zero-downtime rolling, blue-green, and canary deployments.
   - Non-destructive database migrations with automatic rollback checkpointing.
   - Live smoke testing, health probe monitoring, and manifest generation.
5. **Intelligent Observability, AIOps & Self-Healing**:
   - Continuous anomaly detection across CPU, memory, latency, and error rates.
   - Automated root-cause analysis (RCA) and authorized self-healing remediation plans.
6. **Autonomous Maintenance & Continuous Improvement**:
   - Scans for dependency CVEs, code smells, technical debt, and test coverage gaps.
   - Creates pull requests with verified regression-tested patches.
7. **Commercial Multi-Tenant SaaS Platform**:
   - Strict tenant isolation, Argon2id auth, JWT RBAC (`Owner`, `Admin`, `Developer`, `Billing`, `Viewer`).
   - Subscription lifecycle (Starter, Team, Professional, Enterprise) and Stripe/Razorpay integration.
   - Real-time FinOps metering, unit economics tracking, and hard spending caps.
8. **Hypercare Launch Center**:
   - Dedicated Next.js operations view monitoring all 18 production metrics, live incident feed, and cohort rollouts.

---

## Architecture & 97-Agent Registry

```
                               ┌────────────────────────────────────────────────┐
                               │           Next.js Management Dashboard         │
                               │   (Projects, Agents, Workflows, Hypercare)    │
                               └───────────────────────┬────────────────────────┘
                                                       │ HTTP / WebSocket / SSE
                               ▼                       ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              FastAPI Master Orchestration Engine                       │
│  ┌───────────────────────┐  ┌───────────────────────┐  ┌────────────────────────────┐  │
│  │ Dynamic Agent Selector│  │ 97 Specialist Agents  │  │ Dual-Loop Safety Engine    │  │
│  └───────────────────────┘  └───────────────────────┘  └────────────────────────────┘  │
│  ┌───────────────────────┐  ┌───────────────────────┐  ┌────────────────────────────┐  │
│  │ Autonomous Code Gen   │  │ Release Governor      │  │ SaaS Tenant & FinOps Meter │  │
│  └───────────────────────┘  └───────────────────────┘  └────────────────────────────┘  │
└──────────────────────────────────────────────┬─────────────────────────────────────────┘
                                               │
                    ┌──────────────────────────┴──────────────────────────┐
                    ▼                                                     ▼
┌───────────────────────────────────────┐             ┌───────────────────────────────────┐
│     Persistent Storage & Cache        │             │   Cloud Workers / Execution Pool  │
│  • PostgreSQL (Multi-Tenant Schema)   │             │   • Containerized Fargate Workers │
│  • Redis (Celery & Rate Limiting)     │             │   • Worktree Git Scaffolder       │
│  • AWS S3 (Artifact Store)            │             │   • Pytest / Playwright Runners   │
└───────────────────────────────────────┘             └───────────────────────────────────┘
```

The system organizes 97 specialist agents into 10 functional divisions:
- **Architecture & Systems (Roles 1–10):** Solution Architect, Cloud Architect, Database Modeler, API Designer, Security Architect...
- **Frontend & UI/UX (Roles 11–20):** UI/UX Designer, React Engineer, Next.js Specialist, TailwindCSS Expert, State Manager...
- **Backend & APIs (Roles 21–32):** Python/FastAPI Engineer, Node.js Specialist, GraphQL Engineer, Microservices Architect...
- **Mobile Development (Roles 33–40):** React Native Developer, Flutter Specialist, iOS/Swift, Android/Kotlin...
- **Data & AI (Roles 41–50):** Data Engineer, ETL Pipeline Specialist, ML Ops, Vector Search Engineer...
- **DevOps & Cloud (Roles 51–62):** Terraform Engineer, Kubernetes Specialist, CI/CD Pipeline Architect, AWS CloudOps...
- **Quality Assurance & Testing (Roles 63–74):** Test Architect, Unit Test Specialist, E2E Playwright Expert, Security QA...
- **Security & Compliance (Roles 75–84):** Pen Tester, SAST/DAST Auditor, GDPR/SOC2 Compliance Officer...
- **Observability & SRE (Roles 85–92):** Site Reliability Engineer, Distributed Tracing Specialist, Incident Commander...
- **FinOps & Maintenance (Roles 93–97):** Cloud FinOps Lead, Dependency Maintenance Specialist, Refactoring Engineer...

---

## System Requirements

- **Operating System:** Linux, macOS, or Windows via WSL2 (Ubuntu 22.04+ recommended)
- **Python:** `3.10` or higher
- **Node.js:** `18.x` or higher (`npm` 9+)
- **Database:** PostgreSQL 15+ (or built-in local SQLite for lightweight development)
- **Cache / Message Broker:** Redis 7+
- **Container Runtime:** Docker & Docker Compose (optional for local standalone dev)
- **Git:** 2.30+

---

## Quick Start

### 1. One-Click Automated Startup

The fastest way to launch the full platform locally (backend + database initialization + frontend dashboard):

```bash
# Clone the repository
git clone https://github.com/naresh-palle/AI-SOFTWARE-FACTORY.git
cd AI-SOFTWARE-FACTORY

# Run the automated launch script
chmod +x scripts/start_factory.sh
./scripts/start_factory.sh
```

This script:
1. Detects and activates your Python `.venv`.
2. Initializes the database schema and syncs the 97-agent catalog.
3. Launches the FastAPI backend at `http://127.0.0.1:8000`.
4. Launches the Next.js Dashboard at `http://localhost:3000`.

---

### 2. Docker Compose Startup

To spin up the complete cloud worker environment (FastAPI Backend, PostgreSQL 16, Redis 7, and Cloud Worker):

```bash
# Start all core services in detached mode
docker-compose up -d

# Verify container status
docker-compose ps
```

To run the full multi-worker cloud simulation:
```bash
docker compose -f docker/docker-compose.cloud.yml up -d
```

---

### 3. Manual Setup (Backend + Frontend)

#### Step 3A: Backend Setup
```bash
# 1. Create and activate a Python 3.10 virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 3. Create your local environment file
cp .env.example .env

# 4. Initialize database schema & sync the 97 specialist agents
python -c "import asyncio; from factory.core.database import init_db; asyncio.run(init_db())"
python -m factory.cli.main init

# 5. Start the FastAPI orchestrator
uvicorn factory.api.main:app --host 0.0.0.0 --port 8000 --reload
```

#### Step 3B: Frontend Dashboard Setup
```bash
cd dashboard

# Install frontend dependencies
npm install

# Start Next.js development server
npm run dev
```

Visit `http://localhost:3000` to open the Management Dashboard.

---

## How to Use

### A. Web Management Dashboard (UI)

Open `http://localhost:3000` in your browser.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 🏭 AI SOFTWARE FACTORY                         [👤 Elena Rostova (Acme Pro)]│
├─────────────────┬───────────────────────────────────────────────────────────┤
│ 📊 Overview     │ Active Projects: 12      Agents Online: 97   Uptime: 99.98%│
│ 📁 Projects     │                                                           │
│ 🤖 Agent Hub    │ [ + Submit New Requirement ]                              │
│ ⚙️ Pipelines    │ ───────────────────────────────────────────────────────── │
│ 🚀 Releases     │ 📝 Project Title: Real-time FinTech Trading Terminal      │
│ 🩺 Health & Ops │ 🎯 Platform Target: [ Fullstack Web & API  ▼ ]            │
│ 🛡️ Security Audit│ 💬 Requirement Text:                                      │
│ 💳 SaaS & Billing│    "Create an enterprise settlement API with WebSocket   │
│ 🚀 Hypercare    │     price streaming and Stripe recurring billing."         │
│                 │                                                           │
│                 │ [ 🚀 Execute Autonomous Development Pipeline ]            │
└─────────────────┴───────────────────────────────────────────────────────────┘
```

1. **Submit a Requirement**:
   - Navigate to **Projects** → click **New Project**.
   - Input your requirement in natural language and select the target platform (`Website`, `Fullstack`, `Android`, `iOS`).
   - Click **Execute Pipeline**.
2. **Monitor Stage Progression (Stages 1–23)**:
   - View real-time agent selection, architectural specification generation, and dependency resolutions.
   - Review pending human approval gates (e.g. database migration or production release sign-off).
3. **Inspect Generated Code & Worktrees**:
   - Access the Git worktree viewer to inspect frontend components, backend endpoints, and unit test suites generated by specialist agents.
4. **Access the Hypercare Launch Center**:
   - Click **Hypercare** in the sidebar to review production metrics:
     - 18 live telemetry indicators (P95 latency, error rates, tenant count).
     - Cohort onboarding progress and circuit-breaker status.
     - Real-time FinOps COGS breakdown and gross margin percentages.

---

### B. Command Line Interface (CLI)

The factory provides an interactive CLI under `factory.cli.main`:

#### 1. Inspect the 97-Agent Registry
```bash
# List all 97 agents
python -m factory.cli.main agents

# Filter agents by category
python -m factory.cli.main agents --category "Frontend & UI/UX"
python -m factory.cli.main agents --category "DevOps & Cloud"
```

#### 2. Analyze a Natural-Language Requirement
```bash
python -m factory.cli.main analyze "Build a real-time crypto portfolio tracker with price alerts" --platform fullstack
```
*Output will display the dynamically selected tech stack, architecture tiers, and the subset of specialist agent roles assigned to the project.*

#### 3. Run the Autonomous Development Pipeline
```bash
python -m factory.cli.main run "Build an inventory management service with barcode scanning" --name "InventoryPro" --platform fullstack
```

#### 4. Check Project Status & Deliverables
```bash
python -m factory.cli.main status <PROJECT_ID>
```

#### 5. Grant Operator Approval
```bash
python -m factory.cli.main approve <APPROVAL_ID> --notes "Approved by Lead Architect"
```

---

### C. REST API Interactive Docs

Explore, test, and integrate with the platform via Swagger UI:
- **Interactive Swagger UI:** `http://127.0.0.1:8000/docs`
- **ReDoc Documentation:** `http://127.0.0.1:8000/redoc`

#### Key API Modules:
| Endpoint Group | Description |
| :--- | :--- |
| `POST /api/v1/saas/auth/register` | Register new SaaS tenant and administrator |
| `POST /api/v1/saas/auth/token` | Obtain JWT Bearer access and refresh tokens |
| `POST /api/v1/projects/` | Create a new project from natural-language requirement |
| `POST /api/v1/orchestrator/pipeline/{id}/run` | Execute the 23-stage autonomous pipeline |
| `GET /api/v1/approvals/pending` | List pending governance sign-off gates |
| `POST /api/v1/approvals/{id}/decide` | Approve or reject a pending stage action |
| `POST /api/v1/deployment/release` | Trigger governed zero-downtime release |
| `POST /api/v1/maintenance/scan` | Trigger autonomous vulnerability & refactor scan |
| `GET /api/v1/hypercare/overview` | Fetch all 18 live production hypercare metrics |

---

### D. Python SDK / Programmatic API

You can import and orchestrate the factory directly inside your own Python code:

```python
import asyncio
from factory.core.database import get_db_session, init_db
from factory.orchestrator.master import MasterOrchestrator
from factory.agents.dynamic_selector import DynamicAgentSelector
from factory.deployment.production_release_governor import ProductionReleaseGovernor

async def build_software():
    await init_db()
    
    # 1. Dynamic Analysis & Technology Selection
    selector = DynamicAgentSelector()
    plan = await selector.analyze_and_select(
        requirement_text="High-throughput payment reconciliation microservice",
        platform_target="backend"
    )
    print(f"Selected Stack: {plan.technology_stack.backend} + {plan.technology_stack.database}")
    print(f"Assigned Agents: {len(plan.selected_agent_roles)} specialist roles")

    # 2. Master Orchestrator Pipeline
    orchestrator = MasterOrchestrator()
    project = await orchestrator.initialize_project(
        name="Settlement Core",
        requirement_text="High-throughput payment reconciliation microservice",
        platform_target="backend"
    )
    
    # Execute stages 1 through 10
    state = await orchestrator.run_pipeline(project.id, stop_at_stage=10)
    print(f"Pipeline Stage: {state.current_stage}/23 | Cost: ${state.total_cost_usd:.2f}")

asyncio.run(build_software())
```

---

## Development Lifecycle & 23 Stages

The autonomous development pipeline progresses deterministically through 23 stages:

```
Stage 01: Requirement Ingestion & Semantic Analysis
Stage 02: Architectural & Functional Specification
Stage 03: Technology Stack & Framework Selection
Stage 04: Dynamic Specialist Agent Selection (Roles 1..97)
Stage 05: Development Plan & Dependency Graph
Stage 06: Human Approval Gate #1 (Architecture & Budget)
Stage 07: Git Repository & Workspace Isolation
Stage 08: Database Schema Design & Non-Destructive Migrations
Stage 09: Backend API Scaffolding & Business Logic
Stage 10: Frontend Component Generation & State Wiring
Stage 11: Mobile Application Build (When Requested)
Stage 12: Third-Party & Social API Integrations (Meta, Google, X)
Stage 13: Dual-Loop Regression Safety & Unit Testing
Stage 14: Integration & End-to-End Testing (Playwright)
Stage 15: Security Audit, SAST (Bandit), & Secret Scrubbing
Stage 16: Human Approval Gate #2 (Pre-Deployment Sign-off)
Stage 17: Containerization & Artifact Packaging (Docker/ECR)
Stage 18: Deployment to Staging Environment
Stage 19: Smoke Testing & Health Probe Verification
Stage 20: Governed Zero-Downtime Production Deployment
Stage 21: Live Payment & Subscription Verification
Stage 22: AIOps Continuous Observability & Self-Healing
Stage 23: Autonomous Maintenance & Continuous Improvement
```

---

## Testing & Quality Verification

The repository enforces mandatory regression safety. Every pull request and release is validated across 115 comprehensive automated test suites:

```bash
# Activate your virtual environment
source .venv/bin/activate

# Run the complete test suite (Phases 1 through 11)
pytest tests/ -v

# Run the 19-Step Commercial Production Launch Validation Harness
pytest tests/test_production_launch_19_steps.py -v

# Run performance benchmarking script
python scripts/performance_benchmark.py
```

### Commercial Production Launch Verification (19 Steps)
The test harness `tests/test_production_launch_19_steps.py` verifies all 19 operational launch gates:
- Production deployment execution & rolling update.
- HTTPS domain configuration with HSTS and security headers.
- Multi-tenant customer registration and Argon2id authentication.
- Organization hierarchy and team partitioning.
- Strict tenant isolation (0 cross-tenant records exposed).
- Git worktree creation and commit generation.
- Live payment gateway ($1.00 micro-charge) authorization and reconciliation.
- Quota metering and hard spending cap enforcement.
- Self-healing automated RCA and disaster recovery snapshot creation.

---

## Configuration & Environment Variables

Create a `.env` file in the project root:

```ini
# ==========================================
# Application & Environment Settings
# ==========================================
ENVIRONMENT=production                 # development | staging | production
LOG_LEVEL=INFO
SECRET_KEY=change-me-to-a-secure-random-64-char-string
WORKER_AUTH_TOKEN=change-me-to-a-secure-worker-token

# ==========================================
# Database Configuration
# ==========================================
# Local SQLite default:
DATABASE_URL=sqlite+aiosqlite:///./ai_factory.db
# Or PostgreSQL for production:
# DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/ai_factory

# ==========================================
# Redis & Celery Workers
# ==========================================
REDIS_URL=redis://localhost:6379/0

# ==========================================
# AI Model & LLM Providers
# ==========================================
DEFAULT_LLM_PROVIDER=mock              # mock | openai | anthropic | gemini | ollama
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
GEMINI_API_KEY=
OLLAMA_BASE_URL=http://localhost:11434

# ==========================================
# Payment Gateways (Stripe & Razorpay)
# ==========================================
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
RAZORPAY_KEY_ID=
RAZORPAY_KEY_SECRET=

# ==========================================
# AWS Cloud & Deployment (Optional)
# ==========================================
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_S3_ARTIFACT_BUCKET=ai-factory-prod-artifacts-encrypted
```

---

## License & Support

- **Status:** Commercial Enterprise Edition (`v1.0.0-prod`)
- **Git Commit:** `c0d0b757356cbfe38d3dbc3b89959384b8c8f394`
- **Full Operational Report:** [phase11_controlled_production_launch_report.md](phase11_controlled_production_launch_report.md)
- **Author:** AI Software Factory Autonomous Architecture Team
- **Support & Issues:** Log customer tickets via the dashboard or submit an issue on GitHub.
