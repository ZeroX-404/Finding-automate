from __future__ import annotations

from dataclasses import dataclass, field



@dataclass
class ResearchStrategy:

    name: str

    score: float

    required_agents: list[str] = field(
        default_factory=list
    )



class AutonomousStrategyPlanner:


    def __init__(
        self,
        calibration=None,
    ):

        self.calibration = calibration



    def available_strategies(
        self,
    ):

        return [

            ResearchStrategy(
                name="STATIC_ANALYSIS",
                score=0.8,
                required_agents=[
                    "ResearcherAgent",
                ],
            ),


            ResearchStrategy(
                name="REPRODUCTION",
                score=0.75,
                required_agents=[
                    "ResearcherAgent",
                    "ValidatorAgent",
                ],
            ),


            ResearchStrategy(
                name="CRITIC_REVIEW",
                score=0.7,
                required_agents=[
                    "CriticAgent",
                ],
            ),

        ]



    def select_strategy(
        self,
        objective: str,
    ):

        strategies = (
            self.available_strategies()
        )


        return max(
            strategies,
            key=lambda x:
                x.score,
        )
