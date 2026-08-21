from __future__ import annotations

from pathlib import Path
from typing import Any

from .evidence_executor import EvidenceExecutorError, run_evidence_request_executor
from .ledger import Ledger
from .policy import ScopePolicy
from .promotion_case import run_promotion_acceptance_case


def run_executor_acceptance_case(
    ledger: Ledger,
    repo_root: str | Path,
    semgrep_json: str | Path,
    *,
    policy: ScopePolicy,
    repo_commit: str | None = None,
) -> dict[str, Any]:
    promotion = run_promotion_acceptance_case(
        ledger,
        repo_root,
        semgrep_json,
        policy=policy,
        repo_commit=repo_commit,
    )
    if not promotion["all_expected"]:
        raise RuntimeError("promotion acceptance stage failed before evidence executor")

    by_artifact = {item["artifact"]: item for item in promotion["decisions"]}
    executions: list[dict[str, Any]] = []
    for artifact in ("direct_input.py", "guarded.py"):
        decision = by_artifact[artifact]
        result = run_evidence_request_executor(
            ledger,
            decision["proposal_id"],
            repo_root,
            policy=policy,
            repo_commit=repo_commit,
        )
        executions.append(
            {
                "artifact": artifact,
                "proposal_id": decision["proposal_id"],
                "completed_count": result["completed_count"],
                "unsupported_count": result["unsupported_count"],
                "operations": [item["operation"] for item in result["requests"]],
                "evidence_ids": result["evidence_ids"],
                "pass": result["completed_count"] == 2 and result["unsupported_count"] == 0,
            }
        )

    repeated = run_evidence_request_executor(
        ledger,
        by_artifact["direct_input.py"]["proposal_id"],
        repo_root,
        policy=policy,
        repo_commit=repo_commit,
    )

    rejected_blocked = False
    rejected_error = None
    try:
        run_evidence_request_executor(
            ledger,
            by_artifact["constant.py"]["proposal_id"],
            repo_root,
            policy=policy,
            repo_commit=repo_commit,
        )
    except EvidenceExecutorError as exc:
        rejected_blocked = True
        rejected_error = str(exc)

    with ledger.connect() as conn:
        prohibited = {
            row[0]: row[1]
            for row in conn.execute(
                "SELECT kind, COUNT(*) FROM objects WHERE kind IN ('Claim','Validation','Finding') GROUP BY kind"
            ).fetchall()
        }
        counts = {
            kind: conn.execute("SELECT COUNT(*) FROM objects WHERE kind=?", (kind,)).fetchone()[0]
            for kind in ("ResearchProposal", "ProposalDecision", "Experiment", "Evidence")
        }
        neutral_executor_evidence = conn.execute(
            """
            SELECT COUNT(*) FROM objects
            WHERE kind='Evidence'
              AND json_extract(payload_json, '$.provenance.created_by')='evidence-request-executor-v1.9'
              AND json_extract(payload_json, '$.relation')='NEUTRAL'
            """
        ).fetchone()[0]

    audit = ledger.audit()
    return {
        "case": "evidence-request-executor-v1.9",
        "executions": executions,
        "idempotent_recheck": {
            "proposal_id": repeated["proposal_id"],
            "idempotent_reuse": repeated["idempotent_reuse"],
            "evidence_ids": repeated["evidence_ids"],
        },
        "rejected_proposal_blocked": rejected_blocked,
        "rejected_error": rejected_error,
        "neutral_executor_evidence": neutral_executor_evidence,
        "counts": counts,
        "all_expected": (
            all(item["pass"] for item in executions)
            and repeated["idempotent_reuse"] is True
            and rejected_blocked
            and neutral_executor_evidence == 4
        ),
        "prohibited_objects": prohibited,
        "audit": audit,
    }
