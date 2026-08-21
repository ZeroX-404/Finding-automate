from __future__ import annotations

from research_agent.agents import (
    ResearcherAgent,
    CriticAgent,
)


class Orchestrator:


    def __init__(self):

        self.agents = {
            "REQUEST_MORE_EVIDENCE":
                ResearcherAgent(),

            "RUN_VALIDATION":
                CriticAgent(),

            "PROMOTE_FINDING":
                CriticAgent(),
        }


    def dispatch(
        self,
        decision,
        context: dict,
    ):

        agent = self.agents.get(
            decision.action
        )

        if agent is None:
            raise ValueError(
                f"No agent for {decision.action}"
            )

        return agent.execute(
            context
        )
