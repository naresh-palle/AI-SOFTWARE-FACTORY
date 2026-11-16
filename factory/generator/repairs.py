"""
Narrow, reviewable repairs for generated test failures.

A repair is applied only when the traceback matches a known safe edit.
Unknown failures are left unchanged so the loop cannot invent a fix.
"""

from typing import Optional

from factory.generator.workspace import WorkspaceManager


def apply_repair(workspace: WorkspaceManager, failure_output: str) -> Optional[str]:
    """Return a description of the file change, or None when no safe repair exists."""
    if "name 'HEALTH_STATUS' is not defined" in failure_output:
        relative = "backend/app/main.py"
        if not workspace.exists(relative):
            return None
        source = workspace.read_file(relative)
        if "HEALTH_STATUS =" in source:
            return None
        if "HEALTH_STATUS" not in source and "health_check" not in source:
            return None
        workspace.write_file(relative, 'HEALTH_STATUS = "healthy"\n' + source)
        return "Defined HEALTH_STATUS in backend/app/main.py"

    if "No module named 'app.integrations'" in failure_output or 'No module named "app.integrations"' in failure_output:
        relative = "backend/app/integrations/__init__.py"
        if workspace.exists(relative):
            return None
        workspace.write_file(relative, '"""Third-party API integrations."""\n')
        return "Added the integrations package initializer"

    return None
