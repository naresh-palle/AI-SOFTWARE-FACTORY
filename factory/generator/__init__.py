"""
Autonomous Code Generation Engine for AI Software Factory.
Coordinates isolated workspace management, GitHub operations, specialist code generation workers,
automated testing, and bug-fixing loops.
"""

from factory.generator.workspace import WorkspaceManager
from factory.generator.github_service import GitHubAutomationService
from factory.generator.testing_engine import AutomatedTestingEngine, TestRunOutcome
from factory.generator.engine import CodeGenerationEngine

__all__ = [
    "WorkspaceManager",
    "GitHubAutomationService",
    "AutomatedTestingEngine",
    "TestRunOutcome",
    "CodeGenerationEngine",
]
