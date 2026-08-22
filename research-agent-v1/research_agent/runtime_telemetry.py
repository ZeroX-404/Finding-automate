from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4


def utc_now():
    return datetime.now(
        timezone.utc
    ).isoformat()


@dataclass
class RuntimeTelemetry:

    run_id: str = field(
        default_factory=lambda:
            f"RUN-{uuid4().hex[:12]}"
    )

    status: str = "STARTED"

    events: list[dict] = field(
        default_factory=list
    )

    started_at: str = field(
        default_factory=utc_now
    )

    finished_at: str | None = None


    def record(
        self,
        event_type: str,
        payload: dict | None = None,
    ):

        self.events.append(
            {
                "type": event_type,
                "payload": payload or {},
                "timestamp": utc_now(),
            }
        )


    def complete(self):

        self.status = "COMPLETED"

        self.finished_at = utc_now()


    def fail(
        self,
        error: str,
    ):

        self.status = "FAILED"

        self.record(
            "ERROR",
            {
                "message": error
            }
        )

        self.finished_at = utc_now()
