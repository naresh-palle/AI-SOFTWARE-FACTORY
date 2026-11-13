"""
Factory CLI Interface.
Enables local execution, requirement submission, and orchestration monitoring.
"""

import asyncio
import sys
import click
from rich.console import Console
from rich.table import Table

from factory.agents.dynamic_selector import DynamicAgentSelector
from factory.agents.registry import AGENT_CATALOG, AgentRegistry
from factory.core.database import get_db_session, init_db
from factory.models.schema import ApprovalRecord
from factory.orchestrator.master import MasterOrchestrator

console = Console()


@click.group()
def cli():
    """Autonomous AI Software Development Factory CLI."""
    pass


@cli.command("init")
def init_cmd():
    """Initialize database and sync agent catalog."""
    async def _run():
        console.print("[bold green]Initializing Factory Database...[/bold green]")
        await init_db()
        async with get_db_session() as session:
            count = await AgentRegistry.sync_with_db(session)
        console.print(f"[bold green]Initialized successfully! {count} new agents synced.[/bold green]")

    asyncio.run(_run())


@cli.command("agents")
@click.option("--category", default=None, help="Filter by category")
def list_agents_cmd(category):
    """List specialist agents from the catalog."""
    table = Table(title="Specialist Agent Registry (Roles 1..97)")
    table.add_column("#", style="cyan", width=4)
    table.add_column("Role Title", style="bold white")
    table.add_column("Category", style="yellow")
    table.add_column("Capabilities", style="green")

    agents = AgentRegistry.get_all_agents()
    if category:
        agents = AgentRegistry.get_by_category(category)

    for a in agents:
        table.add_row(
            str(a.role_number),
            a.role_title,
            a.category,
            ", ".join(a.capabilities[:2])
        )

    console.print(table)


@cli.command("analyze")
@click.argument("requirement", type=str)
@click.option("--platform", default="fullstack", help="Target platform (website, android, ios, fullstack)")
def analyze_cmd(requirement, platform):
    """Analyze a requirement in natural language and display dynamic selections."""
    async def _run():
        selector = DynamicAgentSelector()
        console.print(f"[bold blue]Analyzing Requirement:[/bold blue] {requirement}\n")
        plan = await selector.analyze_and_select(requirement, platform)

        console.print(f"[bold green]Title:[/bold green] {plan.project_title}")
        console.print(f"[bold green]Estimated Monthly Cost:[/bold green] ${plan.estimated_monthly_cost_usd:.2f}")

        # Tech Stack Table
        t_table = Table(title="Dynamic Technology Selection")
        t_table.add_column("Layer", style="cyan")
        t_table.add_column("Selected Technology", style="bold white")
        t_table.add_row("Frontend", plan.technology_stack.frontend)
        t_table.add_row("Backend", plan.technology_stack.backend)
        if plan.technology_stack.mobile:
            t_table.add_row("Mobile", plan.technology_stack.mobile)
        t_table.add_row("Database", plan.technology_stack.database)
        if plan.technology_stack.cache:
            t_table.add_row("Cache", plan.technology_stack.cache)
        if plan.technology_stack.payments:
            t_table.add_row("Payments", plan.technology_stack.payments)
        t_table.add_row("Auth", plan.technology_stack.auth)
        t_table.add_row("Cloud Infra", plan.technology_stack.cloud_infra)
        console.print(t_table)

        # Selected Agents
        console.print(f"\n[bold yellow]Selected Specialist Agents ({len(plan.selected_agent_roles)}):[/bold yellow]")
        for role in plan.selected_agent_roles:
            console.print(f"  • {role}")

    asyncio.run(_run())


@cli.command("run")
@click.argument("requirement", type=str)
@click.option("--name", default="Autonomous App", help="Project name")
@click.option("--platform", default="fullstack", help="Target platform")
@click.option("--mode", default="autonomous", help="Execution mode (assisted, semi-autonomous, autonomous)")
@click.option("--stop-at", default=23, type=int, help="Stop at stage (1..23)")
def run_cmd(requirement, name, platform, mode, stop_at):
    """Create project and execute development pipeline."""
    async def _run():
        await init_db()
        orchestrator = MasterOrchestrator()
        console.print(f"[bold cyan]Initializing Project '{name}'...[/bold cyan]")
        project = await orchestrator.initialize_project(
            name=name,
            requirement_text=requirement,
            platform_target=platform,
            execution_mode=mode
        )
        console.print(f"[bold green]Project Created with ID:[/bold green] {project.id}")
        console.print(f"[bold cyan]Starting Execution Pipeline (Stages 1..{stop_at})...[/bold cyan]")

        state = await orchestrator.run_pipeline(project.id, stop_at_stage=stop_at)
        console.print(f"\n[bold green]Pipeline Run Completed.[/bold green]")
        console.print(f"Current Stage: {state.current_stage}/23")
        console.print(f"Total Cost: ${state.total_cost_usd:.2f}")

        if state.pending_approvals:
            console.print("\n[bold yellow]Pending Approvals Required:[/bold yellow]")
            for a in state.pending_approvals:
                console.print(f"  • Approval ID: {a['id']} (Stage {a['stage']}): {a['description']}")

    asyncio.run(_run())


@cli.command("status")
@click.argument("project_id", type=str)
def status_cmd(project_id):
    """Check orchestration status and deliverables for a project."""
    async def _run():
        orchestrator = MasterOrchestrator()
        state = await orchestrator.get_orchestration_state(project_id)
        console.print(f"[bold white]Project: {state.project_name} ({state.project_id})[/bold white]")
        console.print(f"Current Stage: {state.current_stage}/23 | Cost: ${state.total_cost_usd:.2f}")

        table = Table(title="Stage Progression")
        table.add_column("Stage #", width=8)
        table.add_column("Title", style="bold")
        table.add_column("Status")
        table.add_column("Evidence Count")

        for s_num, s_state in sorted(state.stages.items()):
            status_style = "green" if s_state.status == "completed" else "yellow" if s_state.status == "in_progress" else "white"
            table.add_row(
                str(s_num),
                s_state.title,
                f"[{status_style}]{s_state.status}[/{status_style}]",
                str(len(s_state.execution_evidence))
            )
        console.print(table)

    asyncio.run(_run())


if __name__ == "__main__":
    cli()
