from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4



def utc_now():

    return datetime.now(
        timezone.utc
    ).isoformat()



@dataclass
class LearnedCase:

    id: str = field(
        default_factory=lambda:
        f"CASE-{uuid4().hex[:12]}"
    )

    features: list[str] = field(
        default_factory=list
    )

    outcome: str = ""

    confidence: float = 0.0

    created_at: str = field(
        default_factory=utc_now
    )



class AutonomousCaseLearner:


    def __init__(self):

        self.memory = []



    def learn(
        self,
        features: list[str],
        outcome: str,
        confidence: float,
    ):

        case = LearnedCase(
            features=features,
            outcome=outcome,
            confidence=confidence,
        )


        self.memory.append(
            case
        )


        return case



    def successful_cases(self):

        return [
            case
            for case in self.memory
            if case.outcome == "SUCCESS"
        ]



    def failed_cases(self):

        return [
            case
            for case in self.memory
            if case.outcome == "FAILURE"
        ]



    def stats(self):

        total = len(
            self.memory
        )


        success = len(
            self.successful_cases()
        )


        return {

            "total":
                total,

            "success":
                success,

            "failure":
                total - success,

            "success_rate":
                (
                    success / total
                    if total
                    else 0
                ),
        }
