from __future__ import annotations

from dataclasses import dataclass, field



@dataclass
class WorkflowPlan:

    name: str

    agents: list[str]

    success_rate: float = 0.0

    execution_time: float = 0.0



class AutonomousWorkflowOptimizer:


    def __init__(self):

        self.history = []



    def register_result(
        self,
        workflow: WorkflowPlan,
    ):

        self.history.append(
            workflow
        )

        return workflow



    def score(
        self,
        workflow: WorkflowPlan,
    ):

        speed_factor = 1 / (
            workflow.execution_time
            if workflow.execution_time > 0
            else 1
        )


        return round(
            (
                workflow.success_rate
                * 0.8
            )
            +
            (
                speed_factor
                * 0.2
            ),
            4,
        )



    def optimize(
        self,
        workflows: list[WorkflowPlan],
    ):

        if not workflows:

            return None


        return max(
            workflows,
            key=self.score,
        )
