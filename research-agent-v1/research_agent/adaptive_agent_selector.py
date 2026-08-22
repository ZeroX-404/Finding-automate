from __future__ import annotations

from dataclasses import dataclass



@dataclass
class AgentChoice:

    agent: str

    score: float



class AdaptiveAgentSelector:


    def __init__(
        self,
        reputation_engine=None,
        policy_engine=None,
    ):

        self.reputation_engine = (
            reputation_engine
        )

        self.policy_engine = (
            policy_engine
        )



    def candidates(
        self,
        action: str,
    ):

        if self.policy_engine:

            return (
                self.policy_engine
                .select_agents(action)
            )


        return []



    def choose(
        self,
        action: str,
        candidates=None,
    ):

        agents = (
            candidates
            if candidates is not None
            else self.candidates(action)
        )


        if not agents:

            return None



        scored = []


        for agent in agents:

            if self.reputation_engine:

                score = (
                    self.reputation_engine
                    .trust_weight(agent)
                )

            else:

                score = 0.5


            scored.append(
                AgentChoice(
                    agent=agent,
                    score=score,
                )
            )


        return max(
            scored,
            key=lambda x:
            x.score,
        )
