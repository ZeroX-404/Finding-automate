from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4



@dataclass
class ResearchEvent:

    name: str

    metadata: dict = field(
        default_factory=dict
    )



@dataclass
class ResearchSession:


    id: str = field(
        default_factory=lambda:
        f"RUN-{uuid4().hex[:12]}"
    )


    created_at: str = field(
        default_factory=lambda:
        datetime.now(
            timezone.utc
        ).isoformat()
    )


    events: list[ResearchEvent] = field(
        default_factory=list
    )


    def record(
        self,
        name: str,
        metadata: dict | None = None,
    ):

        self.events.append(
            ResearchEvent(
                name=name,
                metadata=metadata or {},
            )
        )


    def export(self):

        return {

            "session_id":
                self.id,

            "created_at":
                self.created_at,

            "events":
                [
                    {
                        "name":
                            e.name,

                        "metadata":
                            e.metadata,
                    }

                    for e in self.events
                ],
        }
