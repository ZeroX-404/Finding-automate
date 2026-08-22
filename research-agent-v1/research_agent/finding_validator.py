from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4



@dataclass
class ValidationResult:

    id: str = field(
        default_factory=lambda:
        f"VAL-{uuid4().hex[:12]}"
    )

    status: str = ""

    confidence: float = 0.0

    reason: str = ""

    next_action: str = ""



class FindingValidationEngine:


    def validate(
        self,
        finding,
    ):

        file_name = (
            finding.file.lower()
        )


        message = (
            finding.message.lower()
        )


        # false positive heuristic

        if (
            "test"
            in file_name
            or
            "example"
            in file_name
            or
            "mock"
            in file_name
        ):

            return ValidationResult(

                status="REJECTED",

                confidence=0.90,

                reason=
                (
                    "Finding appears "
                    "inside test/example data"
                ),

                next_action=
                "Ignore finding",

            )


        if (
            "password"
            in message
            or
            "secret"
            in message
            or
            "credential"
            in message
        ):

            return ValidationResult(

                status="NEEDS_REVIEW",

                confidence=0.60,

                reason=
                (
                    "Sensitive pattern detected "
                    "but impact not proven"
                ),

                next_action=
                (
                    "Trace usage and "
                    "validate runtime impact"
                ),

            )


        return ValidationResult(

            status="REJECTED",

            confidence=0.70,

            reason=
            "Insufficient evidence",

            next_action=
            "Collect additional evidence",

        )
