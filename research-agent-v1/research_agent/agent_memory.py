from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone



@dataclass
class MemoryRecord:

    fingerprint: str

    status: str

    confidence: float

    reason: str

    created_at: str = field(
        default_factory=lambda:
        datetime.now(
            timezone.utc
        ).isoformat()
    )



class AgentMemory:


    def __init__(self):

        self.records = {}



    def remember(
        self,
        fingerprint: str,
        status: str,
        confidence: float,
        reason: str,
    ):

        record = MemoryRecord(

            fingerprint=fingerprint,

            status=status,

            confidence=confidence,

            reason=reason,

        )


        self.records[fingerprint] = record


        return record



    def recall(
        self,
        fingerprint: str,
    ):

        return self.records.get(
            fingerprint
        )



    def contains(
        self,
        fingerprint: str,
    ):

        return (
            fingerprint
            in
            self.records
        )
