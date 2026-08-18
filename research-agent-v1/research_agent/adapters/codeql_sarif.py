from __future__ import annotations

import json
from pathlib import Path

from ..models import Observation, Provenance


def observations_from_sarif(path: str | Path, repo_commit: str | None = None) -> list[Observation]:
    data = json.loads(Path(path).read_text())
    observations: list[Observation] = []

    for run in data.get("runs", []):
        tool = run.get("tool", {}).get("driver", {})
        tool_name = tool.get("name", "CodeQL")
        tool_version = tool.get("version")
        for result in run.get("results", []):
            rule_id = result.get("ruleId", "unknown-rule")
            message = result.get("message", {}).get("text", "SARIF observation")
            locations = result.get("locations", [])
            artifact = None
            location = None
            if locations:
                physical = locations[0].get("physicalLocation", {})
                artifact = physical.get("artifactLocation", {}).get("uri")
                region = physical.get("region", {})
                line = region.get("startLine")
                location = f"{artifact}:{line}" if artifact and line else artifact

            observations.append(
                Observation(
                    summary=f"{rule_id}: {message}",
                    artifact=artifact,
                    location=location,
                    raw=result,
                    provenance=Provenance(
                        created_by="adapter",
                        tool_name=tool_name,
                        tool_version=tool_version,
                        repo_commit=repo_commit,
                    ),
                )
            )
    return observations
