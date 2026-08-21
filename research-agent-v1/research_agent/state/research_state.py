from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class HypothesisStatus(str, Enum):
    ACTIVE = "ACTIVE"
    SUPPORTED = "SUPPORTED"
    REJECTED = "REJECTED"
    DEFERRED = "DEFERRED"


@dataclass
class EvidenceSummary:
    supporting: int = 0
    contradicting: int = 0
    neutral: int = 0


@dataclass
class CriticSummary:
    objections: int = 0
    resolved_objections: int = 0


@dataclass
class ResearchState:
    hypothesis_id: str

    status: HypothesisStatus = HypothesisStatus.ACTIVE

    evidence: EvidenceSummary = field(
        default_factory=EvidenceSummary
    )

    critic: CriticSummary = field(
        default_factory=CriticSummary
    )

    confidence: float = 0.0

    next_action: str | None = None

    created_at: str = field(
        default_factory=lambda:
        datetime.now(timezone.utc).isoformat()
    )

    def add_supporting_evidence(self, count: int = 1):
        self.evidence.supporting += count

    def add_contradicting_evidence(self, count: int = 1):
        self.evidence.contradicting += count

    def add_neutral_evidence(self, count: int = 1):
        self.evidence.neutral += count

    def add_critic_objection(self, resolved=False):
        self.critic.objections += 1

        if resolved:
            self.critic.resolved_objections += 1

    def to_dict(self):
        return {
            "hypothesis_id": self.hypothesis_id,
            "status": self.status.value,
            "confidence": self.confidence,
            "evidence": {
                "supporting": self.evidence.supporting,
                "contradicting": self.evidence.contradicting,
                "neutral": self.evidence.neutral,
            },
            "critic": {
                "objections": self.critic.objections,
                "resolved": self.critic.resolved_objections,
            },
            "next_action": self.next_action,
            "created_at": self.created_at,
        }
