from __future__ import annotations

from dataclasses import dataclass, field



@dataclass
class ResearchStrategy:

    name: str

    steps: list[str]

    success_rate: float = 0.0

    usage_count: int = 0



class SelfImprovingStrategyEngine:


    def __init__(self):

        self.strategies = []



    def register(
        self,
        strategy: ResearchStrategy,
    ):

        self.strategies.append(
            strategy
        )

        return strategy



    def evaluate(
        self,
        strategy: ResearchStrategy,
    ):

        if strategy.usage_count == 0:

            return 0.5


        return strategy.success_rate



    def improve(
        self,
        candidates: list[ResearchStrategy],
    ):

        if not candidates:

            return None


        return max(
            candidates,
            key=self.evaluate,
        )



    def recommend(
        self,
        candidates: list[ResearchStrategy],
    ):

        best = self.improve(
            candidates
        )


        if not best:

            return None


        return {

            "strategy":
                best.name,

            "steps":
                best.steps,

            "confidence":
                best.success_rate,

        }
