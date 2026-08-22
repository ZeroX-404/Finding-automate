from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4
from datetime import datetime, timezone



@dataclass
class GeneratedEvidence:

    id: str = field(
        default_factory=lambda:
        f"EVD-{uuid4().hex[:12]}"
    )

    source: str = ""

    evidence_type: str = ""

    description: str = ""

    confidence: float = 0.0

    created_at: str = field(
        default_factory=lambda:
        datetime.now(
            timezone.utc
        ).isoformat()
    )



class EvidenceGenerationPipeline:


    def __init__(self):

        self.evidence = []



    def from_scanner_report(
        self,
        report,
    ):

        generated = []


        for file in report.suspicious_files:

            evidence = GeneratedEvidence(

                source=file,

                evidence_type=
                "STATIC_ANALYSIS",

                description=
                (
                    "Suspicious pattern detected "
                    f"in {file}"
                ),

                confidence=0.6,

            )


            self.evidence.append(
                evidence
            )


            generated.append(
                evidence
            )


        return generated



    def count(self):

        return len(
            self.evidence
        )
