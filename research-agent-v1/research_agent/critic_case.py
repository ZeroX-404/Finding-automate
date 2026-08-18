from __future__ import annotations

from pathlib import Path
from typing import Any

from .contextual_case import EXPECTED as CONTEXT_EXPECTED
from .contextual_case import run_contextual_acceptance_case
from .critic_engine import run_independent_critic
from .ledger import Ledger
from .models import CriticVerdict
from .policy import ScopePolicy


EXPECTED = {
    "direct_input.py": CriticVerdict.SUPPORTS.value,
    "constant.py": CriticVerdict.REJECTS.value,
    "guarded.py": CriticVerdict.CHALLENGES.value,
    "indirect.py": CriticVerdict.SUPPORTS.value,
    "unreachable.py": CriticVerdict.REJECTS.value,
    "false_signal.py": CriticVerdict.REJECTS.value,
}


def run_critic_acceptance_case(
    ledger: Ledger,
    repo_root: str | Path,
    semgrep_json: str | Path,
    *,
    policy: ScopePolicy,
    repo_commit: str | None = None,
) -> dict[str, Any]:
    contextual = run_contextual_acceptance_case(
        ledger,
        repo_root,
        semgrep_json,
        policy=policy,
        repo_commit=repo_commit,
    )
    if not contextual["all_expected"]:
        raise RuntimeError("contextual acceptance stage failed before critic review")

    reviews: list[dict[str, Any]] = []
    for item in contextual["assessments"]:
        result = run_independent_critic(
            ledger,
            item["assessment_id"],
            repo_commit=repo_commit,
        )
        expected = EXPECTED[item["artifact"]]
        reviews.append(
            {
                "artifact": item["artifact"],
                "context_status": item["status"],
                "context_expected": CONTEXT_EXPECTED[item["artifact"]],
                "critic_id": result["critic_id"],
                "verdict": result["verdict"],
                "expected": expected,
                "pass": result["verdict"] == expected,
                "objections": result["objections"],
                "missing_evidence": result["missing_evidence"],
            }
        )

    with ledger.connect() as conn:
        prohibited = {
            row[0]: row[1]
            for row in conn.execute(
                "SELECT kind, COUNT(*) FROM objects WHERE kind IN ('Claim','Validation','Finding') GROUP BY kind"
            ).fetchall()
        }
        critic_count = conn.execute(
            "SELECT COUNT(*) FROM objects WHERE kind='CriticRecord'"
        ).fetchone()[0]

    audit = ledger.audit()
    return {
        "case": "independent-critic-v1.5",
        "review_count": len(reviews),
        "critic_object_count": critic_count,
        "reviews": reviews,
        "all_expected": all(item["pass"] for item in reviews),
        "prohibited_objects": prohibited,
        "audit": audit,
    }
