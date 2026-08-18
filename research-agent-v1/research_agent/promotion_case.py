from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .ledger import Ledger, sha256_text
from .models import (
    EdgeRelation,
    Method,
    MethodKind,
    ProposalDisposition,
    ProposalKind,
    Provenance,
    ResearchProposal,
)
from .policy import ScopePolicy
from .promotion_gate import run_proposal_gate
from .researcher_case import run_researcher_acceptance_case


def _make_refinement_fixture(
    ledger: Ledger,
    base_proposal_id: str,
    *,
    policy: ScopePolicy,
    repo_commit: str | None,
) -> ResearchProposal:
    base = ledger.get(base_proposal_id)["payload"]
    statement = (
        "The eval sink in direct_input.py receives a function parameter whose external influence "
        "remains unresolved and should be traced interprocedurally before exploitability is assessed."
    )
    output = {
        "schema_version": "1",
        "proposal_kind": "HYPOTHESIS_REFINEMENT",
        "disposition": "CONTINUE",
        "statement": statement,
        "falsifier": "Interprocedural analysis proves the parameter cannot be influenced across the relevant trust boundary or is effectively constrained before the sink.",
        "prediction": "Call-site analysis will either identify an externally influenced path to the parameter or deterministically weaken this refinement.",
        "requested_evidence": ["Call-site and trust-boundary data-flow evidence."],
        "assumptions": ["Function-parameter origin alone does not establish attacker control."],
    }
    output_json = json.dumps(output, sort_keys=True, separators=(",", ":"))
    output_hash = sha256_text(output_json)
    input_hash = sha256_text(f"promotion-fixture:{base_proposal_id}")

    method = Method(
        name="V1.7 promotion-gate acceptance refinement fixture",
        kind=MethodKind.MODEL_REASONING,
        version="1.7-fixture",
        deterministic=True,
        parameters={"fixture": True, "can_create_finding": False},
        provenance=Provenance(
            created_by="promotion-case-fixture",
            model_id="mock-refinement-fixture-v1.7",
            tool_name="fixture-model",
            tool_version="1.7",
            repo_commit=repo_commit,
            input_hash=input_hash,
            output_hash=output_hash,
            scope_id=policy.scope_id,
            parent_ids=[base["subject_id"], base["assessment_id"], base["critic_id"]],
        ),
    )
    ledger.put(method)

    proposal = ResearchProposal(
        subject_id=base["subject_id"],
        assessment_id=base["assessment_id"],
        critic_id=base["critic_id"],
        method_id=method.id,
        proposal_kind=ProposalKind.HYPOTHESIS_REFINEMENT,
        disposition=ProposalDisposition.CONTINUE,
        statement=output["statement"],
        falsifier=output["falsifier"],
        prediction=output["prediction"],
        requested_evidence=output["requested_evidence"],
        assumptions=output["assumptions"],
        model_output_hash=output_hash,
        repository_content_treated_as_data=True,
        schema_version="1",
        provenance=Provenance(
            created_by="promotion-case-fixture",
            model_id="mock-refinement-fixture-v1.7",
            tool_name="fixture-model",
            tool_version="1.7",
            repo_commit=repo_commit,
            input_hash=input_hash,
            output_hash=output_hash,
            scope_id=policy.scope_id,
            parent_ids=[base["subject_id"], base["assessment_id"], base["critic_id"], method.id],
        ),
    )
    ledger.put(proposal)
    ledger.add_edge(proposal.id, EdgeRelation.PROPOSES_FOR, proposal.subject_id)
    ledger.add_edge(proposal.id, EdgeRelation.DERIVED_FROM, proposal.assessment_id)
    ledger.add_edge(proposal.id, EdgeRelation.DERIVED_FROM, proposal.critic_id)
    ledger.add_edge(proposal.id, EdgeRelation.USES_METHOD, method.id)
    return proposal


def run_promotion_acceptance_case(
    ledger: Ledger,
    repo_root: str | Path,
    semgrep_json: str | Path,
    *,
    policy: ScopePolicy,
    repo_commit: str | None = None,
) -> dict[str, Any]:
    researcher = run_researcher_acceptance_case(
        ledger,
        repo_root,
        semgrep_json,
        policy=policy,
        repo_commit=repo_commit,
    )
    if not researcher["all_expected"]:
        raise RuntimeError("researcher acceptance stage failed before proposal gate")

    by_artifact = {item["artifact"]: item for item in researcher["proposals"]}

    expected = {
        "direct_input.py": "DEFER",
        "guarded.py": "DEFER",
        "constant.py": "REJECT",
    }
    decisions: list[dict[str, Any]] = []
    for artifact, expected_decision in expected.items():
        result = run_proposal_gate(
            ledger,
            by_artifact[artifact]["proposal_id"],
            policy=policy,
            repo_commit=repo_commit,
        )
        decisions.append(
            {
                "artifact": artifact,
                "proposal_id": result["proposal_id"],
                "decision_id": result["decision_id"],
                "decision": result["decision"],
                "expected": expected_decision,
                "pass": result["decision"] == expected_decision,
                "reason_codes": result["reason_codes"],
            }
        )

    accepted_fixture = _make_refinement_fixture(
        ledger,
        by_artifact["direct_input.py"]["proposal_id"],
        policy=policy,
        repo_commit=repo_commit,
    )
    accepted = run_proposal_gate(
        ledger,
        accepted_fixture.id,
        policy=policy,
        repo_commit=repo_commit,
    )
    repeated = run_proposal_gate(
        ledger,
        accepted_fixture.id,
        policy=policy,
        repo_commit=repo_commit,
    )

    with ledger.connect() as conn:
        prohibited = {
            row[0]: row[1]
            for row in conn.execute(
                "SELECT kind, COUNT(*) FROM objects WHERE kind IN ('Claim','Validation','Finding') GROUP BY kind"
            ).fetchall()
        }
        counts = {
            kind: conn.execute("SELECT COUNT(*) FROM objects WHERE kind=?", (kind,)).fetchone()[0]
            for kind in ("ResearchProposal", "ProposalDecision", "Hypothesis")
        }

    audit = ledger.audit()
    accepted_ok = (
        accepted["decision"] == "ACCEPT"
        and bool(accepted["promoted_hypothesis_id"])
        and repeated["idempotent_reuse"] is True
        and repeated["decision_id"] == accepted["decision_id"]
        and repeated["promoted_hypothesis_id"] == accepted["promoted_hypothesis_id"]
    )

    return {
        "case": "proposal-promotion-gate-v1.7",
        "decisions": decisions,
        "accepted_refinement": {
            "proposal_id": accepted_fixture.id,
            **accepted,
            "pass": accepted_ok,
        },
        "idempotent_recheck": repeated,
        "counts": counts,
        "all_expected": all(item["pass"] for item in decisions) and accepted_ok,
        "prohibited_objects": prohibited,
        "audit": audit,
    }
