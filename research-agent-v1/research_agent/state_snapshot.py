from __future__ import annotations

from datetime import datetime, timezone


def create_state_snapshot(
    state,
    parent_ids=None,
):
    return {
        "kind": "ResearchStateSnapshot",
        "hypothesis_id": state.hypothesis_id,
        "status": state.status.value,
        "confidence": state.confidence,
        "evidence": {
            "supporting": state.evidence.supporting,
            "contradicting": state.evidence.contradicting,
            "neutral": state.evidence.neutral,
        },
        "critic": {
            "objections": state.critic.objections,
            "resolved": state.critic.resolved_objections,
        },
        "next_action": state.next_action,
        "parent_ids": parent_ids or [],
        "created_at": datetime.now(
            timezone.utc
        ).isoformat(),
    }
