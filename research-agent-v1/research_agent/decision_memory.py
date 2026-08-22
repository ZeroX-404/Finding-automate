from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4



def utc_now():

    return datetime.now(
        timezone.utc
    ).isoformat()



@dataclass
class DecisionRecord:

    id: str = field(
        default_factory=lambda:
        f"DM-{uuid4().hex[:12]}"
    )

    decision: str = ""

    confidence: float = 0.0

    agents: list[str] = field(
        default_factory=list
    )

    outcome: str | None = None

    created_at: str = field(
        default_factory=utc_now
    )



class DecisionMemory:


    def __init__(self):

        self.records = []



    def store(
        self,
        record: DecisionRecord,
    ):

        self.records.append(
            record
        )

        return record



    def find_similar(
        self,
        decision: str,
    ):

        return [
            r
            for r in self.records
            if r.decision == decision
        ]



    def update_outcome(
        self,
        record_id: str,
        outcome: str,
    ):

        for record in self.records:

            if record.id == record_id:

                record.outcome = outcome

                return record


        raise ValueError(
            "Decision record not found"
        )



    def agent_accuracy(
        self,
        agent: str,
    ):

        relevant = [
            r
            for r in self.records
            if agent in r.agents
            and r.outcome is not None
        ]


        if not relevant:

            return 0.0


        success = len(
            [
                r
                for r in relevant
                if r.outcome == "SUCCESS"
            ]
        )


        return success / len(relevant)
