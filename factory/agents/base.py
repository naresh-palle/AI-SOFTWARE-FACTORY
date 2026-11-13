"""
Base Specialist Agent Definition and Execution Context.
"""

import abc
import time
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from factory.core.logger import logger
from factory.llm.provider import BaseLLMProvider, get_llm_provider


class AgentContext(BaseModel):
    project_id: str
    task_id: Optional[str] = None
    stage: int
    requirement_text: str
    parsed_spec: Dict[str, Any] = Field(default_factory=dict)
    architecture: Dict[str, Any] = Field(default_factory=dict)
    workspace_path: Optional[str] = None
    input_data: Dict[str, Any] = Field(default_factory=dict)


class AgentResult(BaseModel):
    agent_name: str
    status: str  # success, failed, awaiting_approval
    summary: str
    deliverables: Dict[str, Any] = Field(default_factory=dict)
    execution_evidence: str  # Strict requirement: verifiable evidence
    input_tokens: int = 0
    output_tokens: int = 0
    latency_ms: int = 0


class BaseAgent(abc.ABC):
    """Abstract base class for all specialist agents."""

    def __init__(
        self,
        name: str,
        role_number: int,
        role_title: str,
        category: str,
        description: str,
        capabilities: Optional[List[str]] = None,
        llm_provider: Optional[BaseLLMProvider] = None,
    ):
        self.name = name
        self.role_number = role_number
        self.role_title = role_title
        self.category = category
        self.description = description
        self.capabilities = capabilities or []
        self.llm = llm_provider or get_llm_provider()

    @property
    def system_prompt(self) -> str:
        return (
            f"You are the {self.role_title} (#{self.role_number}) in the Autonomous AI Software Development Factory.\n"
            f"Category: {self.category}\n"
            f"Specialization: {self.description}\n"
            f"Capabilities: {', '.join(self.capabilities)}\n"
            "Produce strict, production-grade, verifiable deliverables. Never fake or simulate progress."
        )

    @abc.abstractmethod
    async def execute(self, context: AgentContext) -> AgentResult:
        """Execute agent-specific task logic."""
        pass

    async def run(self, context: AgentContext) -> AgentResult:
        """Standard wrapper tracking execution time, logging, and error handling."""
        start_time = time.time()
        logger.info(f"Agent [{self.role_title}] starting execution for Project {context.project_id} Stage {context.stage}")
        try:
            result = await self.execute(context)
            result.latency_ms = int((time.time() - start_time) * 1000)
            logger.info(f"Agent [{self.role_title}] completed in {result.latency_ms}ms with status: {result.status}")
            return result
        except Exception as e:
            latency = int((time.time() - start_time) * 1000)
            logger.error(f"Agent [{self.role_title}] failed: {e}")
            return AgentResult(
                agent_name=self.name,
                status="failed",
                summary=f"Execution error: {str(e)}",
                execution_evidence=f"Error log: {str(e)}",
                latency_ms=latency
            )
