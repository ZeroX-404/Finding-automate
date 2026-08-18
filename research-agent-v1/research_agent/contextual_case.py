from __future__ import annotations

from pathlib import Path
from typing import Any

from .context_validator import run_python_contextual_validator
from .ledger import Ledger
from .policy import ScopePolicy
from .signal_pipeline import run_semgrep_signal_pipeline


EXPECTED = {
    "direct_input.py": "SUSPICIOUS",
    "constant.py": "WEAKENED",
    "guarded.py": "INCONCLUSIVE",
    "indirect.py": "SUSPICIOUS",
    "unreachable.py": "WEAKENED",
    "false_signal.py": "NO_MATCH",
}


def run_contextual_acceptance_case(
    ledger: Ledger,
    repo_root: str | Path,
    semgrep_json: str | Path,
    *,
    policy: ScopePolicy,
    repo_commit: str | None = None,
) -> dict[str, Any]:
    signals = run_semgrep_signal_pipeline(
        ledger,
        semgrep_json,
        repo_root,
        policy=policy,
        repo_commit=repo_commit,
        context_radius=2,
    )

    assessments: list[dict[str, Any]] = []
    for candidate in signals["candidates"]:
        result = run_python_contextual_validator(
            ledger,
            candidate["hypothesis_id"],
            repo_root,
            policy=policy,
            repo_commit=repo_commit,
        )
        artifact = candidate["artifact"]
        expected = EXPECTED.get(artifact)
        assessments.append(
            {
                "artifact": artifact,
                "hypothesis_id": candidate["hypothesis_id"],
                "assessment_id": result["assessment_id"],
                "status": result["status"],
                "expected": expected,
                "pass": result["status"] == expected,
                "facts": result["facts"],
            }
        )

    with ledger.connect() as conn:
        prohibited = {
            row[0]: row[1]
            for row in conn.execute(
                "SELECT kind, COUNT(*) FROM objects WHERE kind IN ('Claim','Validation','Finding') GROUP BY kind"
            ).fetchall()
        }

    audit = ledger.audit()
    return {
        "case": "contextual-validator-v1.4",
        "signal_count": signals["candidate_count"],
        "assessment_count": len(assessments),
        "assessments": assessments,
        "all_expected": all(item["pass"] for item in assessments),
        "prohibited_objects": prohibited,
        "audit": audit,
    }
