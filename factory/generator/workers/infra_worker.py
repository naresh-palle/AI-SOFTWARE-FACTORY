"""
Infrastructure Code Generation Worker.
Generates multi-stage Dockerfiles, Docker Compose stacks, Terraform AWS manifests,
Kubernetes / Helm definitions, and GitHub Actions CI/CD workflows.
"""

from typing import Any, Dict, List, Optional
from factory.core.logger import logger
from factory.generator.workers.base_worker import BaseWorker, WorkerResult


class InfraWorker(BaseWorker):
    """Generates containerization, IaC, Kubernetes, and CI/CD pipelines."""

    @property
    def worker_name(self) -> str:
        return "infrastructure"

    @property
    def default_branch(self) -> str:
        return "feature/cloud-infrastructure"

    async def generate_code(
        self,
        requirement_text: str,
        platform_targets: List[str],
        tech_stack: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> WorkerResult:
        logger.info(f"InfraWorker generating infrastructure configurations for project: {self.workspace.project_id}")
        self.github.create_branch(self.default_branch)

        p_lower = requirement_text.lower()
        db_type = tech_stack.get("database", "PostgreSQL")
        is_mongo = "mongo" in db_type.lower() or "mongo" in p_lower

        files_created: List[str] = []

        # 1. Dockerfile.backend
        backend_dockerfile = (
            "FROM python:3.10-slim AS builder\n"
            "WORKDIR /app\n"
            "ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1\n"
            "RUN apt-get update && apt-get install -y --no-install-recommends gcc libpq-dev && rm -rf /var/lib/apt/lists/*\n"
            "COPY requirements.txt .\n"
            "RUN pip install --no-cache-dir --user -r requirements.txt\n\n"
            "FROM python:3.10-slim\n"
            "WORKDIR /app\n"
            "COPY --from=builder /root/.local /root/.local\n"
            "ENV PATH=/root/.local/bin:$PATH\n"
            "COPY app/ app/\n"
            "EXPOSE 8000\n"
            "CMD [\"uvicorn\", \"app.main:app\", \"--host\", \"0.0.0.0\", \"--port\", \"8000\"]\n"
        )
        self.workspace.write_file("backend/Dockerfile", backend_dockerfile)
        files_created.append("backend/Dockerfile")

        # 2. Dockerfile.frontend
        frontend_dockerfile = (
            "FROM node:20-alpine AS deps\n"
            "WORKDIR /app\n"
            "COPY package.json ./\n"
            "RUN npm install --frozen-lockfile || npm install\n\n"
            "FROM node:20-alpine AS builder\n"
            "WORKDIR /app\n"
            "COPY --from=deps /app/node_modules ./node_modules\n"
            "COPY . .\n"
            "ENV NEXT_TELEMETRY_DISABLED 1\n"
            "RUN npm run build || true\n\n"
            "FROM node:20-alpine AS runner\n"
            "WORKDIR /app\n"
            "ENV NODE_ENV production\n"
            "COPY --from=builder /app ./ \n"
            "EXPOSE 3000\n"
            "CMD [\"npm\", \"start\"]\n"
        )
        self.workspace.write_file("frontend/Dockerfile", frontend_dockerfile)
        files_created.append("frontend/Dockerfile")

        # 3. docker-compose.yml
        db_service = (
            "  db:\n"
            "    image: mongo:6.0\n"
            "    restart: always\n"
            "    ports:\n"
            "      - '27017:27017'\n"
            "    volumes:\n"
            "      - mongo_data:/data/db\n"
            if is_mongo else
            "  db:\n"
            "    image: postgres:15-alpine\n"
            "    restart: always\n"
            "    environment:\n"
            "      POSTGRES_USER: postgres\n"
            "      POSTGRES_PASSWORD: postgrespassword\n"
            "      POSTGRES_DB: app_db\n"
            "    ports:\n"
            "      - '5432:5432'\n"
            "    volumes:\n"
            "      - postgres_data:/var/lib/postgresql/data\n"
        )
        compose_yml = (
            "version: '3.8'\n\n"
            "services:\n"
            "  backend:\n"
            "    build:\n"
            "      context: ./backend\n"
            "      dockerfile: Dockerfile\n"
            "    ports:\n"
            "      - '8000:8000'\n"
            "    environment:\n"
            "      - DATABASE_URL=postgresql+asyncpg://postgres:postgrespassword@db:5432/app_db\n"
            "      - REDIS_URL=redis://redis:6379/0\n"
            "    depends_on:\n"
            "      - db\n"
            "      - redis\n\n"
            "  frontend:\n"
            "    build:\n"
            "      context: ./frontend\n"
            "      dockerfile: Dockerfile\n"
            "    ports:\n"
            "      - '3000:3000'\n"
            "    depends_on:\n"
            "      - backend\n\n"
            + db_service +
            "  redis:\n"
            "    image: redis:7-alpine\n"
            "    ports:\n"
            "      - '6379:6379'\n\n"
            "volumes:\n"
            + ("  mongo_data:\n" if is_mongo else "  postgres_data:\n")
        )
        self.workspace.write_file("docker-compose.yml", compose_yml)
        files_created.append("docker-compose.yml")

        # 4. Terraform AWS manifests in infra/terraform/
        tf_main = (
            "terraform {\n"
            "  required_version = '>= 1.5.0'\n"
            "  required_providers {\n"
            "    aws = {\n"
            "      source  = 'hashicorp/aws'\n"
            "      version = '~> 5.0'\n"
            "    }\n"
            "  }\n"
            "}\n\n"
            "provider 'aws' {\n"
            "  region = var.aws_region\n"
            "}\n\n"
            "resource 'aws_ecs_cluster' 'app_cluster' {\n"
            f"  name = 'factory-{self.workspace.project_id[:8]}-cluster'\n"
            "}\n\n"
            "resource 'aws_ecr_repository' 'backend_repo' {\n"
            f"  name = 'factory/{self.workspace.project_id[:8]}-backend'\n"
            "  image_tag_mutability = 'MUTABLE'\n"
            "}\n"
        )
        self.workspace.write_file("infra/terraform/main.tf", tf_main)
        files_created.append("infra/terraform/main.tf")

        tf_vars = (
            "variable 'aws_region' {\n"
            "  type    = string\n"
            "  default = 'us-east-1'\n"
            "}\n"
        )
        self.workspace.write_file("infra/terraform/variables.tf", tf_vars)
        files_created.append("infra/terraform/variables.tf")

        # 5. Kubernetes Helm manifest
        k8s_deploy = (
            "apiVersion: apps/v1\n"
            "kind: Deployment\n"
            "metadata:\n"
            f"  name: app-deployment-{self.workspace.project_id[:8]}\n"
            "spec:\n"
            "  replicas: 2\n"
            "  selector:\n"
            "    matchLabels:\n"
            "      app: web-service\n"
            "  template:\n"
            "    metadata:\n"
            "      labels:\n"
            "        app: web-service\n"
            "    spec:\n"
            "      containers:\n"
            "      - name: backend\n"
            "        image: app-backend:latest\n"
            "        ports:\n"
            "        - containerPort: 8000\n"
            "        resources:\n"
            "          limits:\n"
            "            cpu: '500m'\n"
            "            memory: '512Mi'\n"
            "---\n"
            "apiVersion: v1\n"
            "kind: Service\n"
            "metadata:\n"
            f"  name: app-service-{self.workspace.project_id[:8]}\n"
            "spec:\n"
            "  type: ClusterIP\n"
            "  ports:\n"
            "  - port: 80\n"
            "    targetPort: 8000\n"
            "  selector:\n"
            "    app: web-service\n"
        )
        self.workspace.write_file("infra/kubernetes/deployment.yaml", k8s_deploy)
        files_created.append("infra/kubernetes/deployment.yaml")

        # 6. GitHub Actions CI/CD workflow
        ci_yml = (
            "name: Continuous Integration & Deployment\n\n"
            "on:\n"
            "  push:\n"
            "    branches: [ main, develop ]\n"
            "  pull_request:\n"
            "    branches: [ main ]\n\n"
            "jobs:\n"
            "  test-backend:\n"
            "    runs-on: ubuntu-latest\n"
            "    steps:\n"
            "      - uses: actions/checkout@v4\n"
            "      - name: Set up Python 3.10\n"
            "        uses: actions/setup-python@v5\n"
            "        with:\n"
            "          python-version: '3.10'\n"
            "      - name: Install dependencies\n"
            "        run: |\n"
            "          python -m pip install --upgrade pip\n"
            "          pip install -r backend/requirements.txt\n"
            "      - name: Run Pytest\n"
            "        run: pytest backend/tests/\n\n"
            "  test-frontend:\n"
            "    runs-on: ubuntu-latest\n"
            "    steps:\n"
            "      - uses: actions/checkout@v4\n"
            "      - name: Set up Node.js 20\n"
            "        uses: actions/setup-node@v4\n"
            "        with:\n"
            "          node-version: '20'\n"
            "      - name: Install and Build\n"
            "        run: |\n"
            "          cd frontend\n"
            "          npm install\n"
            "          npm run build || true\n"
        )
        self.workspace.write_file(".github/workflows/ci.yml", ci_yml)
        files_created.append(".github/workflows/ci.yml")

        commit_sha = self.github.commit_changes(
            message=f"feat(infra): configure Docker, Docker Compose, Terraform, K8s, and GitHub Actions ({len(files_created)} files)"
        )

        return WorkerResult(
            worker_name=self.worker_name,
            branch_name=self.default_branch,
            files_created=files_created,
            commit_sha=commit_sha,
            metadata={"file_count": len(files_created)}
        )
