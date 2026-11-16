# PALRAM AI × AI Software Factory — Infrastructure & API Readiness

**Date:** 2026-11-17  
**Status:** Ready for soft-launch integration work — **not** production-ready until end-to-end acceptance passes.  
**Decision:** Two repos, API integration, invite-only Studio, no `admin.palramai.in` in v1.

## 1. Current state summary

| Surface | Repo | Hosting today | Status |
|---------|------|---------------|--------|
| Marketing site | `naresh-palle/paleram.ai` | GitHub Pages → `palramai.in` | Live; do not disrupt |
| Factory API | `naresh-palle/AI-SOFTWARE-FACTORY` | Local / Docker only | Not publicly hosted |
| Studio UI (Next.js) | same factory repo `dashboard/` | Local `:3000` | Not publicly hosted |
| Cloud workers | factory `infrastructure/terraform` | AWS ECS worker stack | Workers/VPC only — not API/Studio CDN |

## 2. DNS inspection (no changes applied)

| Host | Observed | Action for later approval |
|------|----------|---------------------------|
| `palramai.in` | GitHub Pages | Keep |
| `www.palramai.in` | CNAME → `npallegoud.github.io` | Keep / canonicalize |
| `app.palramai.in` | **No records** | Future → Studio host |
| `api.palramai.in` | **No records** | Future → FastAPI host |
| `admin.palramai.in` | **No records** | Deferred (use protected admin API/UI) |
| `docs.palramai.in` | **No records** | Deferred |

## 3. API inventory (reuse)

Base: FastAPI `factory.api.main:app` under `/api/v1`

- Core: `/projects`, `/analyze`, orchestrator, approvals, agents, system
- `/saas`: auth, orgs, subscriptions, billing, usage, credentials, support, **admin**
- `/cloud`, `/deployment`, `/observability`, `/maintenance`, `/social`, `/hypercare`
- Public health: `GET /health`

Customer auth: Argon2id/PBKDF2 + JWT (`CustomerAuthManager`).  
Tenant isolation helpers: `TenantManager.validate_tenant_access`.  
Billing: Stripe/Razorpay webhooks already present.

## 4. Readiness gate results

| Gate | Result | Notes |
|------|--------|-------|
| Backend imports | PASS | App loads; 115 tests collect |
| Auth register/login | PASS | JWT auth intact |
| Invite-only soft launch | PASS | `REGISTRATION_MODE=invite_only` + `/admin/tenants/{id}/approve` |
| Tenant isolation (unit) | PASS | Covered by SaaS tests |
| Project APIs tenant-scoped | PASS | Customer JWT scopes create/list; dashboard sends bearer |
| CORS for palramai domains | PASS | Explicit allowlist; credentials enabled |
| Admin SaaS endpoints auth | PASS | Operator token or platform-admin JWT required |
| `X-Tenant-Id` bypass | PASS | Only when `ALLOW_TENANT_HEADER_AUTH` + non-prod |
| HTTPS / public `api`/`app` | NOT STARTED | No DNS/host yet — validate locally first |
| Website Phase E | NEXT | After local API smoke + this commit |

## 5. Hosting readiness (plan only)

Recommended soft-launch topology (apply only after approval):

1. Deploy FastAPI behind TLS as `api.palramai.in`
2. Deploy Next.js Studio as `app.palramai.in`
3. Keep `palramai.in` on GitHub Pages unchanged
4. CORS allowlist: `https://palramai.in`, `https://www.palramai.in`, `https://app.palramai.in`
5. Set `ENVIRONMENT=production`, strong `SECRET_KEY` / `ENCRYPTION_KEY`, `FACTORY_API_TOKEN`, `REGISTRATION_MODE=invite_only`
6. Prefer PostgreSQL + Redis over local SQLite for any shared environment

Terraform in-repo today provisions **worker** infrastructure (VPC/ECS/ECR/S3), not the public API/Studio edge. Choose a separate API/Studio host (or extend Terraform later) without touching apex DNS.

## 6. Security checklist for soft launch

- [x] Keep website free of secrets
- [ ] CORS allowlist (not `*`)
- [ ] Invite-only registration + admin approve
- [ ] Protect `/api/v1/saas/admin/*`
- [ ] Disable header-only tenant auth outside testing
- [ ] Customer JWT required for Studio project APIs; scope by `tenant_id`
- [ ] No `admin.palramai.in` yet; admin via token-protected existing console/API
- [ ] Independent CI: website Pages vs factory `production_release.yml`

## 7. Rollback

- Website: revert `main` on `paleram.ai` (Pages redeploy)
- Factory: revert factory commits; leave marketing apex untouched
- DNS: only add new subdomains later; never point apex away from Pages without explicit approval

## 8. Next increment

1. Implement API readiness fixes + integration tests in factory repo  
2. Local validation (health, invite register, approve, login, create project)  
3. Website Phase E (Studio product pages + CTAs → `app` URL / placeholder)  
4. Hosting/DNS cutover only after acceptance tests + explicit approval  
