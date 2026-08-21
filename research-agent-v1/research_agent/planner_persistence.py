from __future__ import annotations

import hashlib

from .state_models import PlannerDecisionRecord


def make_decision_id(
    hypothesis_id: str,
    action: str
) -> str:

    raw = f"{hypothesis_id}:{action}"

    digest = hashlib.sha256(
        raw.encode()
    ).hexdigest()[:12]

    return f"DEC-{digest}"


def decision_to_record(decision):

    return PlannerDecisionRecord(
        id=make_decision_id(
            decision.hypothesis_id,
            decision.action,
        ),

        hypothesis_id=
            decision.hypothesis_id,

        action=
            decision.action,

        reason_codes=
            decision.reason_codes,

        confidence=
            decision.confidence,
    )
