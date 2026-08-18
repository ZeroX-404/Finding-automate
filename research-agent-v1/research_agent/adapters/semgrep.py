from __future__ import annotations

import json
from pathlib import Path

from ..models import Observation, Provenance


def observations_from_semgrep(path: str | Path, repo_commit: str | None = None) -> list[Observation]:
    data = json.loads(Path(path).read_text())
    observations: list[Observation] = []

    for result in data.get("results", []):
        start = result.get("start", {})
        check_id = result.get("check_id", "unknown-rule")
        file_path = result.get("path")
        line = start.get("line")
        extra = result.get("extra", {})
        message = extra.get("message", "Semgrep observation")

        observations.append(
            Observation(
                summary=f"{check_id}: {message}",
                artifact=file_path,
                location=f"{file_path}:{line}" if file_path and line else file_path,
                raw=result,
                provenance=Provenance(
                    created_by="adapter",
                    tool_name="semgrep",
                    repo_commit=repo_commit,
                ),
            )
        )
    return observations
