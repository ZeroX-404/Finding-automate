from __future__ import annotations

from dataclasses import dataclass



@dataclass
class SupervisorDecision:

    action: str

    reason: str

    iteration: int



class AutonomousResearchSupervisor:


    def __init__(
        self,
        max_iterations: int = 5,
        confidence_threshold: float = 0.85,
    ):

        self.max_iterations = max_iterations

        self.confidence_threshold = (
            confidence_threshold
        )



    def evaluate(
        self,
        confidence: float,
        iteration: int,
    ):


        if confidence >= self.confidence_threshold:

            return SupervisorDecision(
                action="STOP",
                reason=
                "confidence threshold reached",
                iteration=iteration,
            )


        if iteration >= self.max_iterations:

            return SupervisorDecision(
                action="STOP",
                reason=
                "research budget exhausted",
                iteration=iteration,
            )


        if confidence < 0.3:

            return SupervisorDecision(
                action="REFINE_HYPOTHESIS",
                reason=
                "confidence too low",
                iteration=iteration,
            )


        return SupervisorDecision(
            action="CONTINUE",
            reason=
            "more evidence required",
            iteration=iteration,
        )
