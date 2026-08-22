from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4



def utc_now():

    return datetime.now(
        timezone.utc
    ).isoformat()



@dataclass
class TraceEvent:

    id: str = field(
        default_factory=lambda:
        f"TRACE-{uuid4().hex[:12]}"
    )

    event: str = ""

    reason: str = ""

    evidence_ids: list[str] = field(
        default_factory=list
    )

    agent_ids: list[str] = field(
        default_factory=list
    )

    metadata: dict = field(
        default_factory=dict
    )

    created_at: str = field(
        default_factory=utc_now
    )



class ResearchTraceRecorder:


    def __init__(self):

        self.events = []



    def record(
        self,
        event: str,
        reason: str,
        evidence_ids=None,
        agent_ids=None,
        metadata=None,
    ):

        trace = TraceEvent(
            event=event,
            reason=reason,
            evidence_ids=evidence_ids or [],
            agent_ids=agent_ids or [],
            metadata=metadata or {},
        )


        self.events.append(
            trace
        )

        return trace



    def timeline(self):

        return [
            {
                "event":
                    e.event,

                "reason":
                    e.reason,

                "evidence":
                    e.evidence_ids,

                "agents":
                    e.agent_ids,

            }

            for e in self.events
        ]



    def explain(
        self,
        event_id: str,
    ):

        for event in self.events:

            if event.id == event_id:

                return {
                    "decision":
                        event.event,

                    "why":
                        event.reason,

                    "evidence":
                        event.evidence_ids,

                    "agents":
                        event.agent_ids,
                }


        raise ValueError(
            "Trace event not found"
        )
