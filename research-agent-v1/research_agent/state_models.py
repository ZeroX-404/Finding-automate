from __future__ import annotations

from datetime import datetime, timezone
from pydantic import BaseModel, Field


def utc_now():
    return datetime.now(timezone.utc).isoformat()


class ResearchStateSnapshot(BaseModel):

    id: str

    hypothesis_id: str

    status: str

    confidence: float = 0.0

    evidence: dict = Field(
        default_factory=dict
    )

    critic: dict = Field(
        default_factory=dict
    )

    next_action: str | None = None

    provenance: dict = Field(
        default_factory=lambda: {
            "created_at": utc_now()
        }
    )
class PlannerDecisionRecord(BaseModel):

    id: str

    hypothesis_id: str

    action: str

    reason_codes: list[str] = Field(
        default_factory=list
    )

    confidence: float = 0.0

    provenance: dict = Field(
        default_factory=lambda: {
            "created_at": utc_now()
        }
    )
