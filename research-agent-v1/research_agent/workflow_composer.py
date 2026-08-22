from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4



@dataclass
class ResearchWorkflow:

    id: str = field(
        default_factory=lambda:
        f"WF-{uuid4().hex[:12]}"
    )

    proposal_id: str = ""

    steps: list[str] = field(
        default_factory=list
    )



class ResearchWorkflowComposer:


    def __init__(self):

        self.workflows = []



    def compose(
        self,
        proposal,
    ):

        method = proposal.method


        if method == "REPRODUCTION":

            steps = [

                "Analyze affected component",

                "Prepare reproduction procedure",

                "Execute validation test",

                "Collect execution evidence",

                "Validate security impact",

                "Update research finding",

            ]


        elif method == "STATIC_ANALYSIS":

            steps = [

                "Analyze source code",

                "Trace data flow",

                "Collect supporting evidence",

                "Perform validation",

            ]


        else:

            steps = [

                "Gather evidence",

                "Perform investigation",

            ]



        workflow = ResearchWorkflow(

            proposal_id=
                proposal.id,

            steps=steps,

        )


        self.workflows.append(
            workflow
        )


        return workflow



    def count(self):

        return len(
            self.workflows
        )
