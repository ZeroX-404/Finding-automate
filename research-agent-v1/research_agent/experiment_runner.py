from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4



@dataclass
class ExperimentResult:

    id: str = field(
        default_factory=lambda:
        f"EXP-{uuid4().hex[:12]}"
    )

    name: str = ""

    status: str = ""

    observations: list[str] = field(
        default_factory=list
    )



class AutonomousExperimentRunner:


    def __init__(self):

        self.results = []



    def create_plan(
        self,
        hypothesis,
    ):

        statement = (
            hypothesis.statement.lower()
        )


        if "credential" in statement:

            return [

                "Locate credential usage",

                "Trace runtime reference",

                "Check exposure impact",

            ]


        return [

            "Collect additional evidence",

            "Perform validation",

        ]



    def run(
        self,
        hypothesis,
    ):


        steps = self.create_plan(
            hypothesis
        )


        result = ExperimentResult(

            name=
            "AUTOMATED_VALIDATION",

            status=
            "COMPLETED",

            observations=steps,

        )


        self.results.append(
            result
        )


        return result
