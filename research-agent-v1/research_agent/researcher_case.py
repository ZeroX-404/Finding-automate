from __future__ import annotations

from pathlib import Path
from typing import Any

from .critic_case import run_critic_acceptance_case
from .ledger import Ledger
from .policy import ScopePolicy
from .research_models import MockResearchModel
from .researcher import run_model_researcher


EXPECTED = {
    "direct_input.py": ("EVIDENCE_REQUEST", "SEEK_EVIDENCE"),
    "guarded.py": ("EVIDENCE_REQUEST", "SEEK_EVIDENCE"),
    "constant.py": ("HYPOTHESIS_REFINEMENT", "DEPRIORITIZE"),
}


def run_researcher_acceptance_case(
    ledger: Ledger,
    repo_root: str | Path,
    semgrep_json: str | Path,
    *,
    policy: ScopePolicy,
    repo_commit: str | None = None,
) -> dict[str, Any]:
    critic = run_critic_acceptance_case(
        ledger,
        repo_root,
        semgrep_json,
        policy=policy,
        repo_commit=repo_commit,
    )
    if not critic["all_expected"]:
        raise RuntimeError("critic acceptance stage failed before researcher proposals")

    reviews = {item["artifact"]: item for item in critic["reviews"]}
    proposals: list[dict[str, Any]] = []
    model = MockResearchModel()

    for artifact, expected in EXPECTED.items():
        review = reviews[artifact]
        critic_payload = ledger.get(review["critic_id"])["payload"]
        assessment_id = critic_payload["assessment_id"]
        result = run_model_researcher(
            ledger,
            assessment_id,
            review["critic_id"],
            repo_root,
            policy=policy,
            model=model,
            repo_commit=repo_commit,
        )
        proposals.append(
            {
                "artifact": artifact,
                "proposal_id": result["proposal_id"],
                "proposal_kind": result["proposal_kind"],
                "disposition": result["disposition"],
                "expected_kind": expected[0],
                "expected_disposition": expected[1],
                "pass": (
                    result["proposal_kind"] == expected[0]
                    and result["disposition"] == expected[1]
                    and result["repository_content_treated_as_data"] is True
                ),
                "requested_evidence": result["requested_evidence"],
            }
        )

    with ledger.connect() as conn:
        prohibited = {
            row[0]: row[1]
            for row in conn.execute(
                "SELECT kind, COUNT(*) FROM objects WHERE kind IN ('Claim','Validation','Finding') GROUP BY kind"
            ).fetchall()
        }
        proposal_count = conn.execute(
            "SELECT COUNT(*) FROM objects WHERE kind='ResearchProposal'"
        ).fetchone()[0]

    audit = ledger.audit()
    return {
        "case": "model-researcher-v1.6",
        "model_id": model.model_id,
        "proposal_count": proposal_count,
        "proposals": proposals,
        "all_expected": all(item["pass"] for item in proposals),
        "prohibited_objects": prohibited,
        "audit": audit,
    }
