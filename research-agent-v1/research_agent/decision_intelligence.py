from __future__ import annotations

from research_agent.state.decision import (
    ResearchAction,
)


class DecisionIntelligence:

    def __init__(
        self,
        confidence_engine,
    ):

        self.confidence_engine = confidence_engine


    def evaluate(
        self,
        hypothesis_id: str,
        critic_clean: bool = False,
    ) -> dict:

        result = self.confidence_engine.calculate(
            hypothesis_id
        )


        confidence = result["confidence"]

        support = result["supporting_evidence"]

        contradiction = result["contradicting_evidence"]


        if (
            confidence < 0.20
            and contradiction > support
        ):
            action = ResearchAction.DROP_HYPOTHESIS


        elif confidence >= 0.85 and critic_clean:

            action = ResearchAction.PROMOTE_FINDING


        elif contradiction > 0:

            action = ResearchAction.REQUEST_MORE_EVIDENCE


        else:

            action = ResearchAction.CONTINUE_RESEARCH


        return {
            "hypothesis_id": hypothesis_id,
            "confidence": confidence,
            "supporting": support,
            "contradicting": contradiction,
            "critic_clean": critic_clean,
            "action": action,
        }
