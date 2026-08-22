from __future__ import annotations

from enum import StrEnum


class WorkflowStatus(StrEnum):
    CREATED = "CREATED"
    STARTED = "STARTED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class WorkflowTransition:

    def __init__(self, current: WorkflowStatus = WorkflowStatus.CREATED):
        self.current = current

    def transition(self, target: WorkflowStatus):
        allowed = {
            WorkflowStatus.CREATED: [WorkflowStatus.STARTED],
            WorkflowStatus.STARTED: [
                WorkflowStatus.RUNNING,
                WorkflowStatus.FAILED,
            ],
            WorkflowStatus.RUNNING: [
                WorkflowStatus.COMPLETED,
                WorkflowStatus.FAILED,
            ],
            WorkflowStatus.COMPLETED: [],
            WorkflowStatus.FAILED: [],
        }

        if target not in allowed[self.current]:
            raise ValueError(
                f"Invalid transition {self.current} -> {target}"
            )

        self.current = target
        return self.current
