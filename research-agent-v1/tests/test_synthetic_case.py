from research_agent.ledger import Ledger
from research_agent.synthetic_case import run_synthetic_case


def test_synthetic_case_builds_complete_confirmed_lineage(tmp_path):
    ledger = Ledger(tmp_path / "evidence.db")
    result = run_synthetic_case(ledger)

    assert result["state"] == "CONFIRMED"
    assert result["reproducibility"] == {"passes": 3, "attempts": 3}
    assert result["audit"]["ok"] is True

    trace = ledger.trace(result["finding_id"], max_depth=8)
    kinds = {node["kind"] for node in trace["nodes"].values()}
    assert {
        "Source",
        "Method",
        "Observation",
        "Hypothesis",
        "Experiment",
        "Evidence",
        "Claim",
        "CriticRecord",
        "Validation",
        "Finding",
    }.issubset(kinds)

    history = ledger.history(result["finding_id"])
    assert len(history) == 2
    assert history[0]["payload"]["state"] == "UNDER_TEST"
    assert history[1]["payload"]["state"] == "CONFIRMED"


def test_synthetic_case_trace_reaches_source_and_evidence(tmp_path):
    ledger = Ledger(tmp_path / "evidence.db")
    result = run_synthetic_case(ledger)
    trace = ledger.trace(result["finding_id"], max_depth=8)

    assert result["source_id"] in trace["nodes"]
    assert result["evidence_id"] in trace["nodes"]
    assert result["experiment_id"] in trace["nodes"]
    assert result["critic_id"] in trace["nodes"]
    assert result["deterministic_validation_id"] in trace["nodes"]
