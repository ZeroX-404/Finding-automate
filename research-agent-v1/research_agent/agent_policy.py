from __future__ import annotations


class AgentPolicyEngine:

    def __init__(
        self,
        config=None,
    ):
        self.config = config


    def select_agents(
        self,
        action: str,
    ) -> list[str]:

        policies = {

            "REQUEST_MORE_EVIDENCE": [
                "ResearcherAgent",
            ],

            "RUN_VALIDATION": [
                "CriticAgent",
            ],

            "PROMOTE_FINDING": [
                "CriticAgent",
                "ValidatorAgent",
            ],

            "DROP_HYPOTHESIS": [],
        }


        return policies.get(
            action,
            [],
        )


    def can_promote(
        self,
        confidence: float,
        validation_count: int,
    ) -> bool:

        return (
            confidence >= 0.85
            and validation_count >= 2
        )
