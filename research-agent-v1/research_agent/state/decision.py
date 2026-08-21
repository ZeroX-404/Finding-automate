from __future__ import annotations

from enum import Enum

from .research_state import ResearchState


class ResearchAction(str, Enum):
    CONTINUE_RESEARCH = "CONTINUE_RESEARCH"
    REQUEST_MORE_EVIDENCE = "REQUEST_MORE_EVIDENCE"
    PROMOTE_FINDING = "PROMOTE_FINDING"
    DROP_HYPOTHESIS = "DROP_HYPOTHESIS"


class DecisionEngine:
    """
    Deterministic decision layer.

    Tidak membuat klaim vulnerability.
    Hanya menentukan langkah penelitian berikutnya.
    """

    def decide(
        self,
        state: ResearchState,
    ) -> ResearchAction:

        confidence = state.confidence

        unresolved = (
            state.critic.objections
            -
            state.critic.resolved_objections
        )

        supporting = state.evidence.supporting
        contradicting = state.evidence.contradicting


        # Hipotesis sangat lemah
        if confidence < 0.20 and contradicting > supporting:
            return ResearchAction.DROP_HYPOTHESIS


        # Evidence belum cukup
        if unresolved > 0:
            return ResearchAction.REQUEST_MORE_EVIDENCE


        # Bukti kuat dan critic bersih
        if (
            confidence >= 0.85
            and supporting >= 3
            and unresolved == 0
        ):
            return ResearchAction.PROMOTE_FINDING


        return ResearchAction.CONTINUE_RESEARCH
