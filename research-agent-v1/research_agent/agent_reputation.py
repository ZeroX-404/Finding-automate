from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class AgentProfile:

    agent: str

    successes: int = 0

    failures: int = 0

    total_reviews: int = 0


    @property
    def reputation(self):

        if self.total_reviews == 0:
            return 0.5

        return round(
            self.successes /
            self.total_reviews,
            4,
        )



class AgentReputationEngine:


    def __init__(self):

        self.profiles = {}



    def _get_profile(
        self,
        agent: str,
    ):

        if agent not in self.profiles:

            self.profiles[agent] = (
                AgentProfile(
                    agent=agent
                )
            )

        return self.profiles[agent]



    def record_result(
        self,
        agent: str,
        success: bool,
    ):

        profile = self._get_profile(
            agent
        )

        profile.total_reviews += 1


        if success:

            profile.successes += 1

        else:

            profile.failures += 1


        return profile



    def score(
        self,
        agent: str,
    ):

        return (
            self._get_profile(agent)
            .reputation
        )



    def trust_weight(
        self,
        agent: str,
    ):

        score = self.score(
            agent
        )

        return round(
            0.5 + (score * 0.5),
            4,
        )
