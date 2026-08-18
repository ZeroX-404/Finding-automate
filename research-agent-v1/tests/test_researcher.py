from __future__ import annotations

import json
from pathlib import Path

import pytest

from research_agent.context_validator import run_python_contextual_validator
from research_agent.critic_case import run_critic_acceptance_case
from research_agent.critic_engine import run_independent_critic
from research_agent.ledger import Ledger
from research_agent.policy import ScopePolicy
from research_agent.research_models import MockResearchModel, ResearchModel
from research_agent.researcher import (
    ResearcherError,
    build_research_packet,
    run_model_researcher,
)
from research_agent.researcher_case import EXPECTED, run_researcher_acceptance_case
from research_agent.signal_pipeline import run_semgrep_signal_pipeline


ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT / "targets" / "contextual_validator_cases"
SIGNALS = REPO / "signals.json"
POLICY = ROOT / "policy" / "scope.yaml"


def _critic_context(tmp_path):
    ledger = Ledger(tmp_path / "researcher.db")
    policy = ScopePolicy.load(POLICY)
    result = run_critic_acceptance_case(
        ledger,
        REPO,
        SIGNALS,
        policy=policy,
        repo_commit="researcher-test",
    )
    reviews = {item["artifact"]: item for item in result["reviews"]}
    return ledger, policy, reviews


def _ids_for(ledger: Ledger, review: dict):
    critic_id = review["critic_id"]
    critic = ledger.get(critic_id)["payload"]
    return critic["assessment_id"], critic_id, critic["subject_id"]


def test_mock_model_satisfies_research_model_protocol():
    assert isinstance(MockResearchModel(), ResearchModel)


def test_researcher_acceptance_matrix_and_no_authoritative_objects(tmp_path):
    ledger = Ledger(tmp_path / "case.db")
    result = run_researcher_acceptance_case(
        ledger,
        REPO,
        SIGNALS,
        policy=ScopePolicy.load(POLICY),
        repo_commit="researcher-test",
    )
    assert result["all_expected"] is True
    assert result["proposal_count"] == 3
    assert result["prohibited_objects"] == {}
    assert result["audit"]["ok"] is True
    assert {
        item["artifact"]: (item["proposal_kind"], item["disposition"])
        for item in result["proposals"]
    } == EXPECTED


def test_hostile_repository_comment_is_delimited_as_untrusted_data(tmp_path):
    ledger, policy, reviews = _critic_context(tmp_path)
    assessment_id, critic_id, _ = _ids_for(ledger, reviews["direct_input.py"])
    packet = build_research_packet(
        ledger,
        assessment_id,
        critic_id,
        REPO,
        policy=policy,
    )
    assert "ignore previous instructions" in packet.untrusted_repository_data
    assert packet.untrusted_repository_data.startswith("BEGIN_UNTRUSTED_REPOSITORY_DATA")
    assert packet.untrusted_repository_data.endswith("END_UNTRUSTED_REPOSITORY_DATA")
    assert packet.repository_content_trust_zone == "untrusted_repository_content"
    assert any("never instructions" in item for item in packet.trusted_contract)

    result = run_model_researcher(
        ledger,
        assessment_id,
        critic_id,
        REPO,
        policy=policy,
        model=MockResearchModel(),
    )
    assert result["disposition"] == "SEEK_EVIDENCE"
    proposal = ledger.get(result["proposal_id"])["payload"]
    assert proposal["repository_content_treated_as_data"] is True
    assert "safe" not in proposal["statement"].lower()


def test_model_output_cannot_smuggle_finding_fields(tmp_path):
    ledger, policy, reviews = _critic_context(tmp_path)
    assessment_id, critic_id, _ = _ids_for(ledger, reviews["direct_input.py"])

    class MaliciousModel:
        @property
        def model_id(self):
            return "malicious-test-model"

        def propose(self, packet):
            output = MockResearchModel().propose(packet)
            output["finding_state"] = "CONFIRMED"
            return output

    with pytest.raises(ResearcherError, match="schema validation"):
        run_model_researcher(
            ledger,
            assessment_id,
            critic_id,
            REPO,
            policy=policy,
            model=MaliciousModel(),
        )

    with ledger.connect() as conn:
        assert conn.execute("SELECT COUNT(*) FROM objects WHERE kind='ResearchProposal'").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM objects WHERE kind='Finding'").fetchone()[0] == 0


def test_researcher_rejects_critic_for_different_hypothesis(tmp_path):
    ledger, policy, reviews = _critic_context(tmp_path)
    direct_assessment, _, _ = _ids_for(ledger, reviews["direct_input.py"])
    _, constant_critic, _ = _ids_for(ledger, reviews["constant.py"])
    with pytest.raises(ResearcherError, match="critic subject"):
        run_model_researcher(
            ledger,
            direct_assessment,
            constant_critic,
            REPO,
            policy=policy,
            model=MockResearchModel(),
        )


def test_researcher_rejects_changed_source_snapshot(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    source = repo / "app.py"
    source.write_text("def calculate(expression):\n    return eval(expression)\n")
    signal = repo / "semgrep.json"
    signal.write_text(json.dumps({
        "version": "fixture",
        "results": [{
            "check_id": "python.lang.security.audit.eval-detected",
            "path": "app.py",
            "start": {"line": 2, "col": 12},
            "end": {"line": 2, "col": 28},
            "extra": {"message": "Detected use of eval", "metadata": {}, "severity": "WARNING"},
        }],
    }))
    policy = ScopePolicy(
        scope_id="tmp-research",
        repository_roots=[str(repo)],
        capabilities={
            "reason": "ALLOW",
            "repo:read": "ALLOW",
            "scanner:static": "ALLOW",
            "sandbox:execute": "ALLOW",
            "network:read": "DENY",
            "target:test": "DENY",
            "repo:write": "DENY",
            "git:commit": "DENY",
            "external:submit": "DENY",
        },
    )
    ledger = Ledger(tmp_path / "snapshot.db")
    signal_result = run_semgrep_signal_pipeline(
        ledger, signal, repo, policy=policy, repo_commit="snap"
    )
    hypothesis_id = signal_result["candidates"][0]["hypothesis_id"]
    contextual = run_python_contextual_validator(
        ledger, hypothesis_id, repo, policy=policy, repo_commit="snap"
    )
    critic = run_independent_critic(ledger, contextual["assessment_id"], repo_commit="snap")

    source.write_text("def calculate(expression):\n    return 'changed'\n")
    with pytest.raises(ResearcherError, match="source snapshot changed"):
        run_model_researcher(
            ledger,
            contextual["assessment_id"],
            critic["critic_id"],
            repo,
            policy=policy,
            model=MockResearchModel(),
        )


def test_research_proposal_hash_and_provenance_are_recorded(tmp_path):
    ledger, policy, reviews = _critic_context(tmp_path)
    assessment_id, critic_id, _ = _ids_for(ledger, reviews["guarded.py"])
    result = run_model_researcher(
        ledger,
        assessment_id,
        critic_id,
        REPO,
        policy=policy,
        model=MockResearchModel(),
    )
    proposal = ledger.get(result["proposal_id"])["payload"]
    assert proposal["model_output_hash"] == result["model_output_hash"]
    assert proposal["provenance"]["model_id"] == "mock-research-model-v1.6"
    assert proposal["provenance"]["input_hash"] == result["packet_hash"]
    assert proposal["provenance"]["output_hash"] == result["model_output_hash"]


def test_researcher_does_not_create_new_hypothesis(tmp_path):
    ledger, policy, reviews = _critic_context(tmp_path)
    with ledger.connect() as conn:
        before = conn.execute("SELECT COUNT(*) FROM objects WHERE kind='Hypothesis'").fetchone()[0]
    assessment_id, critic_id, _ = _ids_for(ledger, reviews["direct_input.py"])
    run_model_researcher(
        ledger,
        assessment_id,
        critic_id,
        REPO,
        policy=policy,
        model=MockResearchModel(),
    )
    with ledger.connect() as conn:
        after = conn.execute("SELECT COUNT(*) FROM objects WHERE kind='Hypothesis'").fetchone()[0]
    assert after == before


def test_audit_detects_proposal_subject_mismatch(tmp_path):
    ledger, policy, reviews = _critic_context(tmp_path)
    direct_assessment, direct_critic, _ = _ids_for(ledger, reviews["direct_input.py"])
    result = run_model_researcher(
        ledger,
        direct_assessment,
        direct_critic,
        REPO,
        policy=policy,
        model=MockResearchModel(),
    )
    proposal_obj = ledger.get(result["proposal_id"])
    from research_agent.models import ResearchProposal

    proposal = ResearchProposal.model_validate(proposal_obj["payload"])
    _, _, constant_hypothesis = _ids_for(ledger, reviews["constant.py"])
    ledger.put(proposal.model_copy(update={"subject_id": constant_hypothesis}))
    audit = ledger.audit()
    assert audit["ok"] is False
    codes = {issue["code"] for issue in audit["issues"]}
    assert "PROPOSAL_ASSESSMENT_SUBJECT_MISMATCH" in codes
    assert "PROPOSAL_CRITIC_SUBJECT_MISMATCH" in codes


def test_audit_detects_repository_instruction_boundary_violation(tmp_path):
    ledger, policy, reviews = _critic_context(tmp_path)
    assessment_id, critic_id, _ = _ids_for(ledger, reviews["direct_input.py"])
    result = run_model_researcher(
        ledger,
        assessment_id,
        critic_id,
        REPO,
        policy=policy,
        model=MockResearchModel(),
    )
    from research_agent.models import ResearchProposal

    proposal = ResearchProposal.model_validate(ledger.get(result["proposal_id"])["payload"])
    ledger.put(proposal.model_copy(update={"repository_content_treated_as_data": False}))
    audit = ledger.audit()
    assert audit["ok"] is False
    assert "PROPOSAL_REPOSITORY_BOUNDARY_VIOLATION" in {
        issue["code"] for issue in audit["issues"]
    }
