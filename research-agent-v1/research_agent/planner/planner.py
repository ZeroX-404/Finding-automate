from __future__ import annotations

from .models import PlannerDecision


class ResearchPlanner:


    LOW_CONFIDENCE = 0.5
    HIGH_CONFIDENCE = 0.8


    def decide(self, state):

        reasons = []


        #
        # Confidence terlalu rendah
        #
        if state.confidence < self.LOW_CONFIDENCE:

            reasons.append(
                "CONFIDENCE_BELOW_THRESHOLD"
            )

            return PlannerDecision(
                action="REQUEST_MORE_EVIDENCE",
                reason_codes=reasons,
                confidence=state.confidence,
                hypothesis_id=state.hypothesis_id,
            )


        #
        # Ada objection critic
        #
        unresolved = (
            state.critic.objections
            -
            state.critic.resolved_objections
        )


        if unresolved > 0:

            reasons.append(
                "CRITIC_OBJECTION_UNRESOLVED"
            )

            return PlannerDecision(
                action="RUN_VALIDATION",
                reason_codes=reasons,
                confidence=state.confidence,
                hypothesis_id=state.hypothesis_id,
            )


        #
        # Confidence tinggi
        #
        if state.confidence >= self.HIGH_CONFIDENCE:

            reasons.append(
                "CONFIDENCE_THRESHOLD_MET"
            )

            return PlannerDecision(
                action="PROMOTE_FINDING",
                reason_codes=reasons,
                confidence=state.confidence,
                hypothesis_id=state.hypothesis_id,
            )


        return PlannerDecision(
            action="DEFER",
            reason_codes=[
                "INSUFFICIENT_DECISION_SIGNAL"
            ],
            confidence=state.confidence,
            hypothesis_id=state.hypothesis_id,
        )
