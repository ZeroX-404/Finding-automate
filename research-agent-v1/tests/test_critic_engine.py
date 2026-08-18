from pathlib import Path

import pytest

from research_agent.contextual_case import run_contextual_acceptance_case
from research_agent.critic_engine import CriticError, run_independent_critic
from research_agent.critic_case import EXPECTED, run_critic_acceptance_case
from research_agent.ledger import Ledger
from research_agent.models import CriticRecord, CriticVerdict, Provenance
from research_agent.policy import ScopePolicy


ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT / "targets" / "contextual_validator_cases"
SIGNALS = REPO / "signals.json"
POLICY = ROOT / "policy" / "scope.yaml"


def _context(tmp_path):
    ledger = Ledger(tmp_path / "critic.db")
    policy = ScopePolicy.load(POLICY)
    result = run_contextual_acceptance_case(
        ledger, REPO, SIGNALS, policy=policy, repo_commit="critic-test"
    )
    return ledger, result


def test_critic_acceptance_matrix(tmp_path):
    ledger = Ledger(tmp_path / "critic-case.db")
    result = run_critic_acceptance_case(
        ledger,
        REPO,
        SIGNALS,
        policy=ScopePolicy.load(POLICY),
        repo_commit="critic-test",
    )
    assert result["all_expected"] is True
    assert result["critic_object_count"] == 6
    assert result["prohibited_objects"] == {}
    assert result["audit"]["ok"] is True
    assert {item["artifact"]: item["verdict"] for item in result["reviews"]} == EXPECTED


def test_critic_reads_assessment_evidence_and_creates_no_validation(tmp_path):
    ledger, contextual = _context(tmp_path)
    direct = next(item for item in contextual["assessments"] if item["artifact"] == "direct_input.py")
    result = run_independent_critic(ledger, direct["assessment_id"])

    assert result["verdict"] == CriticVerdict.SUPPORTS.value
    critic = ledger.get(result["critic_id"])
    assert critic["kind"] == "CriticRecord"
    assert critic["payload"]["assessment_id"] == direct["assessment_id"]
    assert critic["payload"]["evidence_ids"]

    with ledger.connect() as conn:
        assert conn.execute("SELECT COUNT(*) FROM objects WHERE kind='Validation'").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM objects WHERE kind='Finding'").fetchone()[0] == 0


def test_guard_is_challenged_not_declared_safe(tmp_path):
    ledger, contextual = _context(tmp_path)
    guarded = next(item for item in contextual["assessments"] if item["artifact"] == "guarded.py")
    result = run_independent_critic(ledger, guarded["assessment_id"])
    assert result["verdict"] == CriticVerdict.CHALLENGES.value
    assert any("guard" in text.lower() for text in result["objections"])
    assert result["missing_evidence"]


def test_constant_and_unreachable_reject_current_hypothesis(tmp_path):
    ledger, contextual = _context(tmp_path)
    by_artifact = {item["artifact"]: item for item in contextual["assessments"]}
    for artifact in ("constant.py", "unreachable.py", "false_signal.py"):
        result = run_independent_critic(ledger, by_artifact[artifact]["assessment_id"])
        assert result["verdict"] == CriticVerdict.REJECTS.value


def test_critic_rejects_wrong_object_kind(tmp_path):
    ledger, contextual = _context(tmp_path)
    hypothesis_id = contextual["assessments"][0]["hypothesis_id"]
    with pytest.raises(CriticError):
        run_independent_critic(ledger, hypothesis_id)


def test_audit_detects_non_independent_critic(tmp_path):
    ledger, contextual = _context(tmp_path)
    item = contextual["assessments"][0]
    assessment = ledger.get(item["assessment_id"])["payload"]
    critic = CriticRecord(
        subject_id=item["hypothesis_id"],
        assessment_id=item["assessment_id"],
        evidence_ids=(
            assessment.get("supporting_evidence_ids", [])
            + assessment.get("contradictory_evidence_ids", [])
            + assessment.get("neutral_evidence_ids", [])
        ),
        verdict=CriticVerdict.INCONCLUSIVE,
        provenance=Provenance(created_by="contextual-validator"),
    )
    ledger.put(critic)
    audit = ledger.audit()
    assert audit["ok"] is False
    assert "CRITIC_NOT_INDEPENDENT" in {issue["code"] for issue in audit["issues"]}
