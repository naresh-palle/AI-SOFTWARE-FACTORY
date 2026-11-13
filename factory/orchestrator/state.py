"""
Master Orchestrator State Models and Stage Definitions.
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class StageEnum(int, Enum):
    STAGE_1_UNDERSTAND_REQUIREMENTS = 1
    STAGE_2_FUNCTIONAL_SPECIFICATIONS = 2
    STAGE_3_RESEARCH_TECHNOLOGIES_APIS = 3
    STAGE_4_DESIGN_ARCHITECTURE = 4
    STAGE_5_DATABASE_ARCHITECTURE = 5
    STAGE_6_UI_UX_DESIGNS = 6
    STAGE_7_GITHUB_REPOSITORY = 7
    STAGE_8_DEV_ENVIRONMENT_SETUP = 8
    STAGE_9_DEVELOP_BACKEND = 9
    STAGE_10_DEVELOP_FRONTEND = 10
    STAGE_11_DEVELOP_MOBILE = 11
    STAGE_12_EXTERNAL_API_INTEGRATIONS = 12
    STAGE_13_AUTHENTICATION = 13
    STAGE_14_SECURITY_CONTROLS = 14
    STAGE_15_AUTOMATED_TESTING = 15
    STAGE_16_FIX_DEFECTS = 16
    STAGE_17_REGRESSION_TESTING = 17
    STAGE_18_CLOUD_INFRASTRUCTURE = 18
    STAGE_19_CONFIGURE_CICD = 19
    STAGE_20_PRODUCTION_APPROVAL = 20
    STAGE_21_DEPLOYMENT = 21
    STAGE_22_PRODUCTION_HEALTH = 22
    STAGE_23_FINAL_DOCUMENTATION = 23


STAGE_TITLES: Dict[int, str] = {
    1: "Understand requirements",
    2: "Prepare functional specifications",
    3: "Research technologies and external APIs",
    4: "Design application architecture",
    5: "Prepare database architecture",
    6: "Create UI/UX designs",
    7: "Create GitHub repository",
    8: "Set up development environment",
    9: "Develop backend",
    10: "Develop frontend",
    11: "Develop mobile applications if requested",
    12: "Implement external API integrations",
    13: "Implement authentication",
    14: "Implement security controls",
    15: "Execute automated testing",
    16: "Fix identified defects",
    17: "Execute regression testing",
    18: "Prepare cloud infrastructure",
    19: "Configure CI/CD",
    20: "Request production approval",
    21: "Deploy after approval",
    22: "Validate production health",
    23: "Generate final documentation",
}


class StageExecutionState(BaseModel):
    stage_number: int
    title: str
    status: str = "pending"  # pending, in_progress, completed, failed, blocked_on_approval
    assigned_agents: List[str] = Field(default_factory=list)
    tasks_count: int = 0
    completed_tasks: int = 0
    execution_evidence: List[str] = Field(default_factory=list)
    artifacts: Dict[str, Any] = Field(default_factory=dict)
    error_message: Optional[str] = None


class OrchestrationState(BaseModel):
    project_id: str
    project_name: str
    requirement_text: str
    execution_mode: str = "autonomous"  # assisted, semi-autonomous, autonomous
    current_stage: int = 1
    total_stages: int = 23
    stages: Dict[int, StageExecutionState] = Field(default_factory=dict)
    total_cost_usd: float = 0.0
    pending_approvals: List[Dict[str, Any]] = Field(default_factory=list)
    is_completed: bool = False
    is_failed: bool = False
