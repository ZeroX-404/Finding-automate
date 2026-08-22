from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4



@dataclass
class ExperimentPlan:

    id: str = field(
        default_factory=lambda:
        f"EXP-{uuid4().hex[:12]}"
    )

    hypothesis: str = ""

    steps: list[str] = field(
        default_factory=list
    )

    evidence_required: list[str] = field(
        default_factory=list
    )

    validation_method: str = ""



class AutonomousExperimentPlanner:


    def __init__(self):

        self.plans = []



    def create_plan(
        self,
        hypothesis: str,
    ):

        plan = ExperimentPlan(
            hypothesis=hypothesis,
            steps=[
                "Analyze target",
                "Generate test procedure",
                "Execute experiment",
                "Collect evidence",
                "Validate result",
            ],
            evidence_required=[
                "Execution output",
                "Reproduction result",
                "Validation record",
            ],
            validation_method=
            "V3_DETERMINISTIC",
        )


        self.plans.append(
            plan
        )


        return plan



    def history(self):

        return self.plans
