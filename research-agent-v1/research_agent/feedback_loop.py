from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4



@dataclass
class FeedbackDecision:

    id: str

    next_action: str

    strategy_update: bool

    confidence_delta: float



class AutonomousFeedbackLoop:


    def __init__(self):

        self.history = []



    def apply(
        self,
        validation_result,
    ):

        status = (
            validation_result.status
        )


        if status == "PASS":

            decision = FeedbackDecision(
                id=f"FDB-{uuid4().hex[:12]}",
                next_action=
                    "STRENGTHEN_HYPOTHESIS",
                strategy_update=False,
                confidence_delta=0.2,
            )


        else:

            decision = FeedbackDecision(
                id=f"FDB-{uuid4().hex[:12]}",
                next_action=
                    "REFINE_HYPOTHESIS",
                strategy_update=True,
                confidence_delta=-0.1,
            )


        self.history.append(
            decision
        )


        return decision



    def latest(self):

        if not self.history:

            return None


        return self.history[-1]
