# AI Software Factory - REST API Reference (v1)

The AI Software Factory provides an enterprise REST API rooted at `/api/v1`. All endpoints enforce TLS 1.3, strict security headers, and sliding-window rate limiting.

Authentication is handled via Bearer JWT tokens (`Authorization: Bearer <token>`) or tenant API keys (`X-API-Key: <key>`).

---

## 1. Authentication & Tenant Identity

### `POST /api/v1/auth/register`
Register a new customer account.
- **Request Body**:
  ```json
  {
    "email": "developer@company.com",
    "password": "StrongPassword123!",
    "full_name": "Jane Doe"
  }
  ```
- **Response** (`201 Created`):
  ```json
  {
    "user_id": "usr_94a2b1c",
    "email": "developer@company.com",
    "full_name": "Jane Doe",
    "tenant_id": "tnt_83f1d9a",
    "created_at": "2026-11-17T01:00:00Z"
  }
  ```

### `POST /api/v1/auth/login`
Authenticate and obtain JWT access token.
- **Rate Limit**: 20 requests / minute per IP.
- **Response** (`200 OK`):
  ```json
  {
    "access_token": "eyJhbGciOi...",
    "token_type": "bearer",
    "expires_in": 3600
  }
  ```

### `DELETE /api/v1/auth/me`
GDPR / DPDP statutory right to be forgotten: cascades deletion of tenant resources.

---

## 2. Multi-Tenant SaaS & Subscriptions

### `POST /api/v1/saas/organizations`
Create a customer organization.
- **Request Body**:
  ```json
  { "name": "Acme Innovations" }
  ```

### `GET /api/v1/saas/organizations/{org_id}/members`
List members belonging to the organization. (Cross-tenant requests return `403 Forbidden` or `404 Not Found`).

### `POST /api/v1/saas/checkout`
Create a Stripe or Razorpay checkout session for plan upgrade.
- **Request Body**:
  ```json
  {
    "org_id": "org_123",
    "plan_tier": "pro",
    "billing_cycle": "monthly",
    "provider": "stripe"
  }
  ```

### `GET /api/v1/saas/usage`
Retrieve current month AI token, compute vCPU hours, and active projects usage against quotas.

### `GET /api/v1/saas/invoices`
List historical billing invoices and download URLs.

---

## 3. Autonomous Project Orchestration

### `POST /api/v1/projects`
Initialize a new software development project.
- **Request Body**:
  ```json
  {
    "name": "E-Commerce Gateway",
    "description": "High-throughput checkout microservice",
    "prompt": "Build a FastAPI microservice with PostgreSQL and Redis",
    "tech_stack": ["python", "fastapi", "postgresql", "redis"]
  }
  ```

### `GET /api/v1/projects/{project_id}`
Retrieve project status, architecture specifications, and current workflow progress.

### `POST /api/v1/projects/{project_id}/generate-code`
Activate the 97-agent autonomous code generation swarm.
- Returns workflow execution ID and real-time task stream.

---

## 4. Deployments & Release Management

### `POST /api/v1/deployments`
Initiate staging or production deployment.
- **Request Body**:
  ```json
  {
    "project_id": "proj_abc123",
    "environment": "staging",
    "artifact_tag": "v1.0.4-staging"
  }
  ```

### `POST /api/v1/deployments/{deployment_id}/rollback`
Trigger emergency deployment rollback to previous healthy artifact tag.

### `GET /api/v1/deployments/{deployment_id}/smoke-tests`
Retrieve real-time smoke test verification results.

---

## 5. Observability & Autonomous Self-Healing

### `GET /api/v1/observability/metrics`
Retrieve OpenTelemetry metrics (RPS, latency p50/p95/p99, error rate %, CPU, RAM).

### `GET /api/v1/observability/incidents`
List active anomalies, detected symptoms, and correlated RCA diagnoses.

### `POST /api/v1/observability/self-heal`
Trigger or authorize automated healing action (restart, circuit-breaker, rollback).

---

## 6. Continuous Maintenance & Dependency Upgrades

### `POST /api/v1/maintenance/scan`
Execute automated security scan (CVEs, outdated libraries, code smells).

### `POST /api/v1/maintenance/patch`
Autonomously generate code patch, run test suite, and open verified GitHub PR.

---

## 7. Disaster Recovery & Backups

### `POST /api/v1/dr/backup`
Generate on-demand encrypted database snapshot with SHA-256 digest verification.

### `POST /api/v1/dr/restore`
Restore database snapshot after cryptographically verifying checksum.
