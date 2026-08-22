from __future__ import annotations

from dataclasses import dataclass



@dataclass
class AgentCalibration:

    agent: str

    reliability: float = 0.5

    samples: int = 0



class SelfCalibrationEngine:


    def __init__(self):

        self.scores = {}



    def update(
        self,
        agent: str,
        success: bool,
    ):

        score = self.scores.get(
            agent,
            AgentCalibration(
                agent=agent
            ),
        )


        old_total = (
            score.reliability
            *
            score.samples
        )


        score.samples += 1


        if success:

            new_value = 1

        else:

            new_value = 0


        score.reliability = (
            old_total + new_value
        ) / score.samples


        self.scores[agent] = score


        return score



    def weight(
        self,
        agent: str,
    ):

        score = self.scores.get(
            agent
        )


        if not score:

            return 0.5


        return score.reliability



    def calibrate_confidence(
        self,
        confidence: float,
        agents: list[str],
    ):

        if not agents:

            return confidence


        weights = [
            self.weight(agent)
            for agent in agents
        ]


        average = sum(weights) / len(weights)


        return round(
            confidence * average,
            4,
        )
