# AI Software Factory - Customer Guide & User Manual

Welcome to the **Autonomous AI Software Factory**—a production-grade, multi-tenant engineering platform that turns plain natural-language requirements into tested, verified, and deployed cloud applications.

---

## 1. Quickstart & Onboarding

### 1.1 Account Registration
1. Navigate to the platform portal or use the REST API (`POST /api/v1/auth/register`).
2. Provide your name, corporate email address, and a secure password (minimum 8 characters).
3. The platform creates your individual customer record with PBKDF2 cryptographic password hashing and generates a tenant ID.

### 1.2 Creating an Organization
1. From the **SaaS & Subscriptions** workspace or via API (`POST /api/v1/saas/organizations`), create your Organization (e.g., `Acme Innovations`).
2. You become the Organization Owner with administrative privileges.
3. Invite team members with role-based access control (`owner`, `admin`, `developer`, `viewer`).

### 1.3 Choosing a Subscription Plan
Navigate to **Commercial Plans** to choose an operating tier:
- **Community Free ($0/mo)**: Ideal for evaluation, includes 100k tokens and 1 active project.
- **Starter ($99/mo)**: 5 active projects, 2M tokens, 97-agent swarm, automated GitHub PRs.
- **Professional ($299/mo)**: 20 active projects, 10M tokens, AWS ECS cloud worker engine, self-healing, CVE auto-patching.
- **Business ($799/mo)**: Unlimited projects, 50M tokens, multi-tenant teams, custom domains, 1h SLA.
- **Enterprise (Custom)**: Dedicated VPC deployment, custom LLMs, SOC 2 / HIPAA compliance, 99.99% SLA.

Test payments can be processed immediately through Stripe or Razorpay sandbox checkout.

---

## 2. Autonomous Project Lifecycle

### 2.1 Submitting a Software Requirement
1. Click **New Project** or navigate to **Create Project**.
2. Give your project a title (e.g., `Fintech Escrow Microservice`).
3. Enter your natural language software requirement in the prompt editor:
   > *"Build a resilient multi-currency escrow microservice with FastAPI, PostgreSQL, Redis caching, Stripe webhooks, automated transaction locking, and Prometheus metrics."*
4. Click **Activate Factory Swarm**.

### 2.2 What the Factory Does Automatically
The platform transitions your project through 23 autonomous verification gates:
1. **Requirement Analysis**: Agent `RequirementsAnalyst` decomposes your prompt into functional requirements, data entities, and acceptance criteria.
2. **Architecture & Stack Selection**: Agent `SolutionsArchitect` selects database schemas, caching layers, and API patterns.
3. **97-Specialist Swarm Code Generation**:
   - Backend agents write FastAPI routes, SQLAlchemy async models, and migrations.
   - Frontend agents generate responsive Next.js views and Shadcn UI components.
   - Database agents design index strategies and constraints.
4. **Automated Verification & SAST**:
   - Test automation agents generate and execute unit/integration Pytest suites.
   - Security agents run Bandit SAST scans to enforce zero High vulnerabilities.
5. **GitHub Integration**:
   - Creates a feature branch and automated Pull Request with structured commit messages.
6. **Governance Gate**:
   - If configured, sensitive production actions pause for Human Approval in the **Human Governance Center**.
7. **Cloud Deployment**:
   - Packages Docker containers and deploys to staging or ECS/Kubernetes.
   - Runs automated smoke tests to verify HTTP 200 health.

---

## 3. Observability & Autonomous Self-Healing

Once your application is deployed:
- **Real-time Telemetry**: Ingests OpenTelemetry traces, HTTP latency, and container CPU/memory metrics.
- **AIOps Root-Cause Analysis (RCA)**: When an anomaly or 5xx error rate occurs, the engine correlates logs and stack traces.
- **3-Tier Self-Healing**:
  - *Tier 1*: Automatic pod restart or cache invalidation.
  - *Tier 2*: Circuit breaker activation and traffic throttling.
  - *Tier 3*: Automatic rollback to the previous known-good deployment artifact.

---

## 4. Continuous Autonomous Maintenance

Your application is continuously kept secure and fresh:
- **CVE Dependency Scans**: Regularly inspects packages for known Common Vulnerabilities and Exposures.
- **Automated Patch Generation**: Generates version-bumped pull requests with passing CI verification.
- **Technical Debt & Performance Profiling**: Detects dead code, inefficient SQL queries, and recommends indexing improvements.

---

## 5. FinOps, Usage Quotas & Billing

- **Usage Metering**: Tracks compute vCPU seconds, AI tokens consumed, and active storage per project.
- **Spending Caps**: Configure hard spending limits in **SaaS Workspace** to prevent unplanned charges.
- **Invoices**: View downloadable monthly invoices with itemized token and compute breakdowns.
- **Data Privacy & GDPR**: Request a full GDPR/DPDP export or complete account deletion from **Settings**.
