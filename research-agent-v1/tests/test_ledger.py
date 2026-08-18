from research_agent.ledger import Ledger
from research_agent.models import (
    Claim,
    EdgeRelation,
    Evidence,
    EvidenceRelation,
    Provenance,
    Source,
    SourceType,
)


def provenance():
    return Provenance(created_by="test")


def test_revision_history_is_append_only(tmp_path):
    ledger = Ledger(tmp_path / "evidence.db")
    ledger.init()

    claim = Claim(statement="first", provenance=provenance())
    ledger.put(claim)
    updated = claim.model_copy(update={"statement": "second"})
    ledger.put(updated)

    history = ledger.history(claim.id)
    assert len(history) == 2
    assert history[0]["payload"]["statement"] == "first"
    assert history[1]["payload"]["statement"] == "second"
    assert history[0]["payload_hash"] != history[1]["payload_hash"]


def test_typed_edge_and_trace(tmp_path):
    ledger = Ledger(tmp_path / "evidence.db")
    ledger.init()

    source = Source(
        source_type=SourceType.FILE,
        reference="src/app.py",
        provenance=provenance(),
    )
    evidence = Evidence(
        description="unsafe data flow",
        source_type="FILE",
        source_ref="src/app.py:10",
        source_id=source.id,
        relation=EvidenceRelation.SUPPORTS,
        provenance=provenance(),
    )
    claim = Claim(statement="input reaches sink", provenance=provenance())

    for obj in (source, evidence, claim):
        ledger.put(obj)

    ledger.add_edge(evidence.id, EdgeRelation.OBSERVED_FROM, source.id)
    ledger.add_edge(evidence.id, EdgeRelation.SUPPORTS, claim.id)

    trace = ledger.trace(claim.id, max_depth=2)
    assert source.id in trace["nodes"]
    assert evidence.id in trace["nodes"]
    assert claim.id in trace["nodes"]


def test_audit_clean_ledger(tmp_path):
    ledger = Ledger(tmp_path / "evidence.db")
    ledger.init()
    claim = Claim(statement="auditable", provenance=provenance())
    ledger.put(claim)

    result = ledger.audit()
    assert result["ok"] is True
    assert result["issues"] == []
