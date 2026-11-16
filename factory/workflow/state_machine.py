"""
Workflow State Machine and Transition Rules.
Defines durable states, allowable transitions, and terminal states.
"""

from enum import Enum
from typing import Set, Dict


class WorkflowJobStatus(str, Enum):
    QUEUED = "queued"
    ASSIGNED = "assigned"
    RUNNING = "running"
    PAUSED = "paused"
    BLOCKED_ON_APPROVAL = "blocked_on_approval"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


# Allowed transitions from current state to destination state
VALID_TRANSITIONS: Dict[WorkflowJobStatus, Set[WorkflowJobStatus]] = {
    WorkflowJobStatus.QUEUED: {
        WorkflowJobStatus.ASSIGNED,
        WorkflowJobStatus.CANCELLED,
    },
    WorkflowJobStatus.ASSIGNED: {
        WorkflowJobStatus.RUNNING,
        WorkflowJobStatus.QUEUED,  # lease expired / worker disconnect
        WorkflowJobStatus.FAILED,
        WorkflowJobStatus.CANCELLED,
    },
    WorkflowJobStatus.RUNNING: {
        WorkflowJobStatus.RUNNING,  # checkpoint update
        WorkflowJobStatus.PAUSED,
        WorkflowJobStatus.BLOCKED_ON_APPROVAL,
        WorkflowJobStatus.COMPLETED,
        WorkflowJobStatus.FAILED,
        WorkflowJobStatus.QUEUED,  # lease expired / recovered
        WorkflowJobStatus.CANCELLED,
    },
    WorkflowJobStatus.PAUSED: {
        WorkflowJobStatus.QUEUED,
        WorkflowJobStatus.CANCELLED,
    },
    WorkflowJobStatus.BLOCKED_ON_APPROVAL: {
        WorkflowJobStatus.QUEUED,  # approved -> re-enqueued for next stage
        WorkflowJobStatus.FAILED,  # rejected
        WorkflowJobStatus.CANCELLED,
    },
    WorkflowJobStatus.COMPLETED: set(),  # terminal
    WorkflowJobStatus.FAILED: {
        WorkflowJobStatus.QUEUED,  # manual retry
    },
    WorkflowJobStatus.CANCELLED: set(),  # terminal
}


def can_transition(current: str, target: str) -> bool:
    try:
        curr_enum = WorkflowJobStatus(current)
        targ_enum = WorkflowJobStatus(target)
    except ValueError:
        return False
    return targ_enum in VALID_TRANSITIONS.get(curr_enum, set())


def is_terminal_status(status: str) -> bool:
    return status in {WorkflowJobStatus.COMPLETED.value, WorkflowJobStatus.CANCELLED.value}
