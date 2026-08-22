from __future__ import annotations

from research_agent.agents import (
    ResearcherAgent,
    CriticAgent,
)


class AgentRouter:

    def __init__(self):

        self.routes = {
            "REQUEST_MORE_EVIDENCE":
                ResearcherAgent(),

            "RUN_VALIDATION":
                CriticAgent(),

            "PROMOTE_FINDING":
                CriticAgent(),
        }


    def resolve(
        self,
        action: str,
    ):

        agent = self.routes.get(action)

        if agent is None:
            raise ValueError(
                f"No agent registered for action: {action}"
            )

        return agent
