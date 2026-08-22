from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4



@dataclass
class ScannerFinding:

    id: str = field(
        default_factory=lambda:
        f"SCAN-{uuid4().hex[:12]}"
    )

    tool: str = ""

    file: str = ""

    rule: str = ""

    severity: str = ""

    message: str = ""



class SecurityScannerAdapter:


    name = "base"



    def scan(
        self,
        repository: str,
    ):

        raise NotImplementedError



class CustomPatternScanner(
    SecurityScannerAdapter
):


    name = "custom"



    def scan(
        self,
        repository: str,
    ):

        from pathlib import Path


        findings = []


        for file in Path(repository).rglob("*"):

            if not file.is_file():

                continue


            try:

                content = file.read_text(
                    errors="ignore"
                )

            except Exception:

                continue



            if "password=" in content.lower():

                findings.append(
                    ScannerFinding(

                        tool=self.name,

                        file=str(file),

                        rule="HARDCODED_SECRET",

                        severity="MEDIUM",

                        message=
                        "Possible hardcoded password",

                    )
                )


        return findings
