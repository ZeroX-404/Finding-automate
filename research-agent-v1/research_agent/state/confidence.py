from __future__ import annotations

from .research_state import ResearchState


class ConfidenceEngine:
    """
    Deterministic confidence calculator.

    Prinsip:
    - Evidence support menaikkan confidence
    - Contradicting evidence menurunkan confidence
    - Unresolved critic objection menurunkan confidence
    - Resolved objection sedikit menaikkan confidence
    """

    def calculate(
        self,
        state: ResearchState,
    ) -> float:

        score = 0.0

        evidence = state.evidence
        critic = state.critic

        # Evidence contribution
        score += evidence.supporting * 0.25
        score -= evidence.contradicting * 0.30

        # Critic contribution
        score += critic.resolved_objections * 0.10

        unresolved = (
            critic.objections
            -
            critic.resolved_objections
        )

        score -= unresolved * 0.15

        # Neutral evidence tidak mengubah confidence

        # Clamp 0-1
        score = max(0.0, min(score, 1.0))

        state.confidence = round(score, 3)

        return state.confidence
