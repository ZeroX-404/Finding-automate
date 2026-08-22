from __future__ import annotations

from dataclasses import dataclass



@dataclass
class ValidationDecision:

    action: str

    reason: str

    continue_research: bool



class ValidationFeedbackLoop:


    def decide(
        self,
        validation,
    ):


        if validation.status == "CONFIRMED":

            return ValidationDecision(

                action="GENERATE_REPORT",

                reason=
                "Finding confirmed",

                continue_research=False,

            )


        if validation.status == "NEEDS_REVIEW":

            return ValidationDecision(

                action="COLLECT_MORE_EVIDENCE",

                reason=
                "Impact not proven",

                continue_research=True,

            )


        if validation.status == "REJECTED":

            return ValidationDecision(

                action="STOP",

                reason=
                "False positive detected",

                continue_research=False,

            )


        return ValidationDecision(

            action="MANUAL_REVIEW",

            reason=
            "Unknown validation state",

            continue_research=False,

        )
