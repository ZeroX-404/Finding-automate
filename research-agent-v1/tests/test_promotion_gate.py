from __future__ import annotations

from pathlib import Path

from research_agent.ledger import Ledger
from research_agent.policy import ScopePolicy
from research_agent.promotion_case import (
    _make_refinement_fixture,
    run_promotion_acceptance_case,
)
from research_agent.promotion_gate import run_proposal_gate
from research_agent.researcher_case import run_researcher_acceptance_case


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PROJECT_ROOT / "targets" / "contextual_validator_cases"
SIGNALS = REPO_ROOT / "signals.json"
POLICY = PROJECT_ROOT / "policy" / "scope.yaml"
COMMIT = "v1.7-test-commit"


def _researcher_ledger(tmp_path):
    ledger = Ledger(tmp_path / "gate.db")
    policy = ScopePolicy.load(POLICY)
    result = run_researcher_acceptance_case(
        ledger,
        REPO_ROOT,
        SIGNALS,
        policy=policy,
        repo_commit=COMMIT,
    )
    assert result["all_expected"] is True
    by_artifact = {item["artifact"]: item for item in result["proposals"]}
    return ledger, policy, by_artifact


def test_evidence_request_is_deferred_not_executed(tmp_path):
    ledger, policy, proposals = _researcher_ledger(tmp_path)
    result = run_proposal_gate(
        ledger,
        proposals["direct_input.py"]["proposal_id"],
        policy=policy,
        repo_commit=COMMIT,
    )
    assert result["decision"] == "DEFER"
    assert "EVIDENCE_REQUEST_REQUIRES_EXECUTOR" in result["reason_codes"]
    assert result["promoted_hypothesis_id"] is None


def test_critic_rejection_blocks_deprioritized_refinement(tmp_path):
    ledger, policy, proposals = _researcher_ledger(tmp_path)
    result = run_proposal_gate(
        ledger,
        proposals["constant.py"]["proposal_id"],
        policy=policy,
        repo_commit=COMMIT,
    )
    assert result["decision"] == "REJECT"
    assert "CRITIC_REJECTS" in result["reason_codes"]
    assert result["promoted_hypothesis_id"] is None


def test_accepted_refinement_creates_gate_authored_hypothesis(tmp_path):
    ledger, policy, proposals = _researcher_ledger(tmp_path)
    fixture = _make_refinement_fixture(
        ledger,
        proposals["direct_input.py"]["proposal_id"],
        policy=policy,
        repo_commit=COMMIT,
    )
    result = run_proposal_gate(
        ledger,
        fixture.id,
        policy=policy,
        repo_commit=COMMIT,
    )
    assert result["decision"] == "ACCEPT"
    promoted = ledger.get(result["promoted_hypothesis_id"])
    assert promoted["kind"] == "Hypothesis"
    provenance = promoted["payload"]["provenance"]
    assert provenance["created_by"] == "proposal-gate-v1.7"
    assert provenance["model_id"] is None
    assert fixture.id in provenance["parent_ids"]


def test_gate_is_idempotent_for_same_proposal(tmp_path):
    ledger, policy, proposals = _researcher_ledger(tmp_path)
    fixture = _make_refinement_fixture(
        ledger,
        proposals["direct_input.py"]["proposal_id"],
        policy=policy,
        repo_commit=COMMIT,
    )
    first = run_proposal_gate(ledger, fixture.id, policy=policy, repo_commit=COMMIT)
    second = run_proposal_gate(ledger, fixture.id, policy=policy, repo_commit=COMMIT)
    assert second["idempotent_reuse"] is True
    assert second["decision_id"] == first["decision_id"]
    assert second["promoted_hypothesis_id"] == first["promoted_hypothesis_id"]


def test_stale_repository_commit_defers_promotion(tmp_path):
    ledger, policy, proposals = _researcher_ledger(tmp_path)
    fixture = _make_refinement_fixture(
        ledger,
        proposals["direct_input.py"]["proposal_id"],
        policy=policy,
        repo_commit=COMMIT,
    )
    result = run_proposal_gate(
        ledger,
        fixture.id,
        policy=policy,
        repo_commit="different-commit",
    )
    assert result["decision"] == "DEFER"
    assert "STALE_REPOSITORY_COMMIT" in result["reason_codes"]


def test_acceptance_case_has_no_claim_validation_or_finding(tmp_path):
    ledger = Ledger(tmp_path / "promotion.db")
    policy = ScopePolicy.load(POLICY)
    result = run_promotion_acceptance_case(
        ledger,
        REPO_ROOT,
        SIGNALS,
        policy=policy,
        repo_commit=COMMIT,
    )
    assert result["all_expected"] is True
    assert result["prohibited_objects"] == {}
    assert result["accepted_refinement"]["decision"] == "ACCEPT"
    assert result["accepted_refinement"]["promoted_hypothesis_id"]
    assert result["audit"]["ok"] is True


def test_duplicate_refinement_is_rejected(tmp_path):
    ledger, policy, proposals = _researcher_ledger(tmp_path)
    fixture1 = _make_refinement_fixture(
        ledger,
        proposals["direct_input.py"]["proposal_id"],
        policy=policy,
        repo_commit=COMMIT,
    )
    first = run_proposal_gate(ledger, fixture1.id, policy=policy, repo_commit=COMMIT)
    assert first["decision"] == "ACCEPT"

    fixture2 = _make_refinement_fixture(
        ledger,
        proposals["direct_input.py"]["proposal_id"],
        policy=policy,
        repo_commit=COMMIT,
    )
    second = run_proposal_gate(ledger, fixture2.id, policy=policy, repo_commit=COMMIT)
    assert second["decision"] == "REJECT"
    assert "DUPLICATE_HYPOTHESIS" in second["reason_codes"]
