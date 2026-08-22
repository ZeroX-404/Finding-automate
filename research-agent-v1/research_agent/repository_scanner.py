from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path



@dataclass
class RepositoryReport:

    path: str

    files: int

    languages: list[str] = field(
        default_factory=list
    )

    suspicious_files: list[str] = field(
        default_factory=list
    )



class RepositoryIntelligenceScanner:


    LANGUAGE_MAP = {

        ".py": "Python",

        ".js": "JavaScript",

        ".ts": "TypeScript",

        ".java": "Java",

        ".go": "Go",

        ".rs": "Rust",

    }



    def scan(
        self,
        repository_path: str,
    ):

        path = Path(
            repository_path
        )


        files = list(
            path.rglob("*")
        )


        code_files = [
            f
            for f in files
            if f.is_file()
        ]


        languages = set()

        suspicious = []


        for file in code_files:

            language = (
                self.LANGUAGE_MAP
                .get(
                    file.suffix
                )
            )


            if language:

                languages.add(
                    language
                )


            try:

                content = (
                    file.read_text(
                        errors="ignore"
                    )
                )


                patterns = [
                    "password=",
                    "secret=",
                    "api_key=",
                ]


                for pattern in patterns:

                    if pattern in content.lower():

                        suspicious.append(
                            str(file)
                        )


            except Exception:

                continue



        return RepositoryReport(

            path=str(path),

            files=len(
                code_files
            ),

            languages=sorted(
                languages
            ),

            suspicious_files=suspicious,

        )
