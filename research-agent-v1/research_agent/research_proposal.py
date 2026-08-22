from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4



@dataclass
class ResearchProposal:

    id: str = field(
        default_factory=lambda:
        f"PRP-{uuid4().hex[:12]}"
    )

    hypothesis_id: str = ""

    method: str = ""

    requested_evidence: list[str] = field(
        default_factory=list
    )

    falsifier: str = ""

    prediction: str = ""



class ResearchProposalGenerator:


    def __init__(self):

        self.proposals = []



    def generate(
        self,
        hypothesis,
    ):

        statement = (
            hypothesis.statement.lower()
        )


        if "credential" in statement:

            method = (
                "REPRODUCTION"
            )

            evidence = [
                "source location",
                "runtime usage analysis",
                "credential impact proof",
            ]

            falsifier = (
                "credential is unused "
                "or non-sensitive"
            )

            prediction = (
                "credential exposure can "
                "be demonstrated"
            )


        else:

            method = (
                "STATIC_ANALYSIS"
            )

            evidence = [
                "code reference",
                "execution evidence",
            ]

            falsifier = (
                "no security impact exists"
            )

            prediction = (
                "additional validation required"
            )


        proposal = ResearchProposal(

            hypothesis_id=
                hypothesis.id,

            method=method,

            requested_evidence=evidence,

            falsifier=falsifier,

            prediction=prediction,

        )


        self.proposals.append(
            proposal
        )


        return proposal



    def count(self):

        return len(
            self.proposals
        )
