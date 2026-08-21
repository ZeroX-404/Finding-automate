from __future__ import annotations

import hashlib

from .state_models import ResearchStateSnapshot


def make_state_id(hypothesis_id: str) -> str:

    digest = hashlib.sha256(
        hypothesis_id.encode()
    ).hexdigest()[:12]

    return f"STATE-{digest}"


def snapshot_from_state(state):

    return ResearchStateSnapshot(
        id=make_state_id(
            state.hypothesis_id
        ),

        hypothesis_id=state.hypothesis_id,

        status=state.status.value,

        confidence=state.confidence,

        evidence={
            "supporting":
                state.evidence.supporting,

            "contradicting":
                state.evidence.contradicting,

            "neutral":
                state.evidence.neutral,
        },

        critic={
            "objections":
                state.critic.objections,

            "resolved":
                state.critic.resolved_objections,
        },

        next_action=state.next_action,
    )
