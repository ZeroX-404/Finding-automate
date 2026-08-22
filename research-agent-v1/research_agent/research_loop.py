from __future__ import annotations

from dataclasses import dataclass, field



@dataclass
class ResearchCycleResult:

    iterations: int

    state: str

    confidence: float

    history: list[dict] = field(
        default_factory=list
    )



class ResearchLoopController:


    def __init__(
        self,
        reasoner=None,
        evolution=None,
        consensus=None,
    ):

        self.reasoner = reasoner
        self.evolution = evolution
        self.consensus = consensus



    def run(
        self,
        hypothesis_id: str,
        max_iterations: int = 5,
    ):


        history = []

        confidence = 0.0

        state = "IN_PROGRESS"


        for iteration in range(
            1,
            max_iterations + 1,
        ):


            evidence_result = {
                "confidence":
                    min(
                        0.2 * iteration,
                        1.0,
                    )
            }


            confidence = (
                evidence_result[
                    "confidence"
                ]
            )


            history.append(
                {
                    "iteration":
                        iteration,

                    "confidence":
                        confidence,
                }
            )


            if confidence >= 0.8:

                state = "CONFIRMED"

                break



        return ResearchCycleResult(
            iterations=len(history),
            state=state,
            confidence=confidence,
            history=history,
        )
