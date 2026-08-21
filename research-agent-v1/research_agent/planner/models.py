from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class PlannerDecision:

    action: str

    reason_codes: list[str] = field(
        default_factory=list
    )

    confidence: float = 0.0

    hypothesis_id: str | None = None


    def to_dict(self):
        return {
            "action": self.action,
            "reason_codes": self.reason_codes,
            "confidence": self.confidence,
            "hypothesis_id": self.hypothesis_id,
        }
