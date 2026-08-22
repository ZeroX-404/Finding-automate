from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4
from datetime import datetime, timezone



def utc_now():

    return datetime.now(
        timezone.utc
    ).isoformat()



@dataclass
class HypothesisRevision:

    id: str = field(
        default_factory=lambda:
        f"HREV-{uuid4().hex[:12]}"
    )

    parent_id: str | None = None

    statement: str = ""

    confidence: float = 0.0

    reason: str = ""

    created_at: str = field(
        default_factory=utc_now
    )



class HypothesisEvolutionEngine:


    def __init__(self):

        self.history = []



    def create_revision(
        self,
        hypothesis_id: str,
        statement: str,
        confidence: float,
        reason: str,
    ):

        revision = HypothesisRevision(
            parent_id=hypothesis_id,
            statement=statement,
            confidence=confidence,
            reason=reason,
        )


        self.history.append(
            revision
        )


        return revision



    def evolve(
        self,
        hypothesis_id: str,
        evidence_result: dict,
    ):

        confidence = (
            evidence_result
            .get(
                "confidence",
                0.0,
            )
        )


        if confidence >= 0.75:

            statement = (
                "Hypothesis strengthened "
                "by supporting evidence"
            )

            reason = "SUPPORTING_EVIDENCE"


        elif confidence <= 0.25:

            statement = (
                "Hypothesis weakened "
                "by contradictory evidence"
            )

            reason = "CONTRADICTING_EVIDENCE"


        else:

            statement = (
                "Hypothesis requires "
                "additional investigation"
            )

            reason = "INSUFFICIENT_SIGNAL"


        return self.create_revision(
            hypothesis_id,
            statement,
            confidence,
            reason,
        )



    def lineage(
        self,
        hypothesis_id: str,
    ):

        return [
            revision
            for revision in self.history
            if revision.parent_id == hypothesis_id
        ]
