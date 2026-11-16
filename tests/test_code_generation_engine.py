"""
Integration and Validation Tests for Autonomous Code Generation Engine.
Verifies all specialist workers, Git automation, workspace isolation,
testing & bug-fixing loops, and executes end-to-end pipelines across 3 real test requirements:
  Case A: Basic business website
  Case B: E-commerce website with authentication & payment gateway (Stripe/Razorpay)
  Case C: Social media analytics platform with Meta & YouTube integrations
"""

import json
import pytest
from pathlib import Path

from factory.core.database import init_db, get_db_session
from factory.core.config import settings
from factory.generator.engine import CodeGenerationEngine
from factory.generator.workspace import WorkspaceManager
from factory.generator.github_service import GitHubAutomationService
from factory.orchestrator.master import MasterOrchestrator


@pytest.mark.asyncio
async def test_workspace_isolation_and_git():
    await init_db()
    project_id = "test-ws-isolation-01"
    ws = WorkspaceManager(project_id)
    assert ws.workspace_path.exists()

    # Verify path traversal protection
    with pytest.raises(ValueError):
        ws.resolve_path("../../escape.txt")

    # Verify write and read
    target, sha = ws.write_file("test.txt", "Hello Factory")
    assert target.exists()
    assert ws.read_file("test.txt") == "Hello Factory"

    # Verify Git automation
    git = GitHubAutomationService(ws)
    init_res = git.init_repository()
    assert init_res["initialized"] is True
    assert init_res["branch"] == "main"
    assert (ws.workspace_path / ".git").is_dir()

    # Verify branch creation and commit
    git.create_branch("feature/test-branch")
    ws.write_file("feature.txt", "New feature code")
    commit_sha = git.commit_changes("feat: add feature code")
    assert commit_sha is not None

    # Verify PR & merge
    pr = git.create_pull_request("feature/test-branch", target_branch="main")
    assert pr["status"] == "open"
    merge_res = git.merge_pull_request("feature/test-branch", target_branch="main")
    assert merge_res["merged"] is True

    # Verify tag release
    tag = git.tag_release("v1.0.0-test", "Release test tag")
    assert tag == "v1.0.0-test"


@pytest.mark.asyncio
async def test_case_a_basic_business_website():
    """Case A: Basic business website (Website only)."""
    await init_db()
    orchestrator = MasterOrchestrator()
    req_text = "Modern corporate website for an architectural consulting firm with portfolio and contact form."
    
    project = await orchestrator.initialize_project(
        name="Case A - Architecture Firm",
        requirement_text=req_text,
        platform_target="website"
    )

    engine = CodeGenerationEngine(project.id)
    git_res = engine.initialize_git()
    assert git_res["initialized"] is True

    # Generate Frontend
    fe_res = await engine.generate_frontend(req_text, ["website"], {})
    assert "frontend/src/app/page.tsx" in fe_res["files_created"]
    assert "frontend/src/components/Navbar.tsx" in fe_res["files_created"]
    assert (engine.workspace.workspace_path / "frontend" / "package.json").exists()
    package_json = json.loads((engine.workspace.workspace_path / "frontend" / "package.json").read_text(encoding="utf-8"))
    assert "autoprefixer" in package_json["devDependencies"]

    # Generate Backend
    be_res = await engine.generate_backend(req_text, ["website"], {})
    assert "backend/app/main.py" in be_res["files_created"]
    assert "backend/tests/test_api.py" in be_res["files_created"]

    # Run automated testing on generated backend
    test_outcome = await engine.run_testing_and_fixing()
    assert test_outcome.status in ["passed", "fixed"]
    assert test_outcome.passed >= 2
    assert test_outcome.failed == 0

    # Verify test_report.json
    report_file = engine.workspace.workspace_path / "test_report.json"
    assert report_file.exists()
    report = json.loads(report_file.read_text(encoding="utf-8"))
    assert report["passed"] >= 2
    assert report["failed"] == 0


@pytest.mark.asyncio
async def test_case_b_ecommerce_with_auth_and_payments():
    """Case B: E-commerce website with authentication & payment gateway (Stripe/Razorpay)."""
    await init_db()
    orchestrator = MasterOrchestrator()
    req_text = "Full-stack e-commerce marketplace for luxury sneakers with customer authentication, product catalog, cart, and Stripe payment gateway."
    
    project = await orchestrator.initialize_project(
        name="Case B - Sneaker Marketplace",
        requirement_text=req_text,
        platform_target="website"
    )

    engine = CodeGenerationEngine(project.id)
    engine.initialize_git()

    # Generate Database
    db_res = await engine.generate_database(req_text, ["website"], {"database": "PostgreSQL"})
    assert "backend/app/models/entities.py" in db_res["files_created"]
    assert "backend/alembic.ini" in db_res["files_created"]

    # Generate Backend
    be_res = await engine.generate_backend(req_text, ["website"], {"database": "PostgreSQL"})
    assert "backend/app/api/auth.py" in be_res["files_created"]
    assert "backend/app/api/v1/endpoints.py" in be_res["files_created"]

    # Generate API Integrations (Stripe / Razorpay)
    api_res = await engine.generate_api_integrations(req_text, ["website"], {})
    assert "backend/app/integrations/payment_gateway.py" in api_res["files_created"]
    payment_code = engine.workspace.read_file("backend/app/integrations/payment_gateway.py")
    assert "create_checkout_session" in payment_code
    assert "create_razorpay_order" in payment_code

    # Generate Frontend
    fe_res = await engine.generate_frontend(req_text, ["website"], {})
    assert "frontend/src/app/products/page.tsx" in fe_res["files_created"]
    assert "frontend/src/app/checkout/page.tsx" in fe_res["files_created"]

    # Generate Infrastructure
    infra_res = await engine.generate_infrastructure(req_text, ["website"], {"database": "PostgreSQL"})
    assert "docker-compose.yml" in infra_res["files_created"]
    assert "infra/terraform/main.tf" in infra_res["files_created"]

    # Run automated testing
    test_outcome = await engine.run_testing_and_fixing()
    assert test_outcome.status in ["passed", "fixed"]
    assert test_outcome.passed >= 3
    assert test_outcome.failed == 0


@pytest.mark.asyncio
async def test_case_c_social_media_analytics():
    """Case C: Social media analytics platform with Meta (Facebook/Instagram) and YouTube integrations."""
    await init_db()
    orchestrator = MasterOrchestrator()
    req_text = "Creator metrics and social media analytics platform integrating Meta Graph API (Facebook and Instagram) and YouTube Data API v3 with cross-platform mobile app."
    
    project = await orchestrator.initialize_project(
        name="Case C - Creator Pulse Analytics",
        requirement_text=req_text,
        platform_target="all"
    )

    engine = CodeGenerationEngine(project.id)
    engine.initialize_git()

    # Generate Database
    db_res = await engine.generate_database(req_text, ["all"], {"database": "MongoDB"})
    assert "backend/app/db/mongodb.py" in db_res["files_created"]
    assert "backend/app/db/redis_cache.py" in db_res["files_created"]

    # Generate API Integrations (Meta + YouTube)
    api_res = await engine.generate_api_integrations(req_text, ["all"], {})
    assert "backend/app/integrations/meta_client.py" in api_res["files_created"]
    assert "backend/app/integrations/youtube_client.py" in api_res["files_created"]
    meta_code = engine.workspace.read_file("backend/app/integrations/meta_client.py")
    assert "get_page_insights" in meta_code
    assert "get_instagram_business_analytics" in meta_code
    assert "send_whatsapp_template_message" in meta_code

    # Generate Mobile
    mob_res = await engine.generate_mobile(req_text, ["all"], {})
    assert "mobile/package.json" in mob_res["files_created"]
    assert "mobile/App.tsx" in mob_res["files_created"]
    assert "mobile/src/services/push_notifications.ts" in mob_res["files_created"]

    # Generate Frontend
    fe_res = await engine.generate_frontend(req_text, ["all"], {})
    assert "frontend/src/app/analytics/page.tsx" in fe_res["files_created"]

    # Generate Backend
    be_res = await engine.generate_backend(req_text, ["all"], {})
    assert "backend/app/main.py" in be_res["files_created"]

    # Run automated testing
    test_outcome = await engine.run_testing_and_fixing()
    assert test_outcome.status in ["passed", "fixed"]
    assert test_outcome.passed >= 3
    assert test_outcome.failed == 0


@pytest.mark.asyncio
async def test_end_to_end_orchestrator_pipeline_with_code_engine():
    """Verify MasterOrchestrator runs stages 1-19 generating real files and code."""
    await init_db()
    orchestrator = MasterOrchestrator()
    project = await orchestrator.initialize_project(
        name="E2E Pipeline Test",
        requirement_text="SaaS platform with subscription payments and interactive analytics dashboard.",
        platform_target="website"
    )

    # Run through stage 19 (stops before stage 20 human approval gate)
    state = await orchestrator.run_pipeline(project.id, stop_at_stage=19)
    assert state.current_stage == 20
    assert state.stages[1].status == "completed"
    assert state.stages[7].status == "completed"
    assert state.stages[9].status == "completed"
    assert state.stages[10].status == "completed"
    assert state.stages[15].status == "completed"
    assert state.stages[18].status == "completed"

    # Check physical deliverables
    ws_dir = settings.PROJECTS_STORAGE_DIR / project.id
    assert (ws_dir / "backend" / "app" / "main.py").exists()
    assert (ws_dir / "frontend" / "package.json").exists()
    assert (ws_dir / "test_report.json").exists()
    assert (ws_dir / "docker-compose.yml").exists()


@pytest.mark.asyncio
async def test_requirements_select_different_stacks_and_agents():
    from factory.agents.dynamic_selector import DynamicAgentSelector

    selector = DynamicAgentSelector()
    website = await selector.analyze_and_select(
        "Modern corporate website for an architectural consulting firm with portfolio and contact form."
    )
    commerce = await selector.analyze_and_select(
        "Full-stack e-commerce marketplace for luxury sneakers with customer authentication, product catalog, cart, and Stripe payment gateway."
    )
    social = await selector.analyze_and_select(
        "Creator metrics and social media analytics platform integrating Meta Graph API (Facebook and Instagram) and YouTube Data API v3 with cross-platform mobile app."
    )

    assert commerce.technology_stack.database == "PostgreSQL"
    assert commerce.technology_stack.payments
    assert website.technology_stack.payments is None
    assert social.technology_stack.database == "MongoDB"
    assert "Payment Gateway Agent" in commerce.selected_agent_roles
    assert "Payment Gateway Agent" not in website.selected_agent_roles
    assert "Meta Developer Agent" in social.selected_agent_roles
    assert "Meta Developer Agent" not in website.selected_agent_roles
    assert set(commerce.selected_agent_roles) != set(social.selected_agent_roles)


def test_commit_refuses_blocked_secret_without_echoing_it():
    project_id = "secret-guard-01"
    workspace = WorkspaceManager(project_id)
    git = GitHubAutomationService(workspace)
    git.init_repository()
    git.create_branch("feature/secret")
    workspace.write_file("config.py", "AWS_KEY = 'AKIAIOSFODNN7EXAMPLE'\n")
    with pytest.raises(RuntimeError) as exc:
        git.commit_changes("feat: add configuration")
    message = str(exc.value)
    assert "config.py" in message
    assert "AKIAIOSFODNN7EXAMPLE" not in message


@pytest.mark.asyncio
async def test_known_repair_is_committed_and_unknown_failure_is_not():
    from factory.generator.sandbox import SandboxResult

    project_id = "repair-loop-01"
    workspace = WorkspaceManager(project_id)
    git = GitHubAutomationService(workspace)
    git.init_repository()
    workspace.write_file("backend/app/main.py", "def health_check():\n    return HEALTH_STATUS\n")
    git.commit_changes("chore: add broken health check")
    engine = CodeGenerationEngine(project_id)

    class ScriptedSandbox:
        def __init__(self):
            self.calls = 0

        def run_backend_tests(self, _workspace):
            self.calls += 1
            if self.calls == 1:
                return SandboxResult(1, "NameError: name 'HEALTH_STATUS' is not defined", "", "failed")
            return SandboxResult(0, "1 passed", "", "passed")

    engine.testing_engine.sandbox = ScriptedSandbox()
    outcome = await engine.testing_engine.run_testing_and_fixing_loop(max_retries=1)
    assert outcome.status == "fixed"
    assert 'HEALTH_STATUS = "healthy"' in workspace.read_file("backend/app/main.py")

    class UnknownFailure:
        def run_backend_tests(self, _workspace):
            return SandboxResult(1, "E   AssertionError: expected 2", "", "failed")

    engine.testing_engine.sandbox = UnknownFailure()
    failed = await engine.testing_engine.run_testing_and_fixing_loop(max_retries=1)
    assert failed.status == "failed"
    rc, log, _ = workspace.run_command(["git", "log", "--oneline"])
    assert rc == 0
    assert "automated defect" not in log.lower()
    assert "expected 2" not in log


def test_host_command_does_not_receive_unrelated_secrets(monkeypatch):
    monkeypatch.setenv("FACTORY_SENTINEL_SECRET", "sentinel-value")
    workspace = WorkspaceManager("env-isolation-01")
    rc, out, err = workspace.run_command(
        ["python3", "-c", "import os; print(os.environ.get('FACTORY_SENTINEL_SECRET', ''))"]
    )
    assert rc == 0
    assert "sentinel-value" not in out
    assert "sentinel-value" not in err


def test_irreversible_commands_are_rejected_before_execution():
    from factory.generator.sandbox import DockerExecutionSandbox

    result = DockerExecutionSandbox().run_rejected_command(["terraform", "apply", "-auto-approve"])
    assert result.status == "rejected"
    assert result.returncode == 126


def test_github_publish_does_not_echo_the_token(monkeypatch):
    from factory.core.config import settings

    monkeypatch.setattr(settings, "GITHUB_TOKEN", "unit-test-token")
    workspace = WorkspaceManager("publish-guard-01")
    git = GitHubAutomationService(workspace)
    git.init_repository()
    seen = {}

    def poster(url, headers, json):
        seen["url"] = url
        seen["authorization"] = headers["Authorization"]
        return {"html_url": "https://github.com/example/factory-test"}

    result = git.publish_repository("factory-test", poster=poster, push=False)
    rendered = json.dumps(result)
    assert result["remote_created"] is True
    assert result["pushed"] is False
    assert seen["url"] == "https://api.github.com/user/repos"
    assert seen["authorization"] == "Bearer unit-test-token"
    assert "unit-test-token" not in rendered
    assert "unit-test-token" not in seen["url"]

