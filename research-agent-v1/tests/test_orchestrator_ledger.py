from research_agent.ledger import Ledger
from research_agent.orchestrator import Orchestrator
from research_agent.planner.models import PlannerDecision


def test_orchestrator_creates_ledger_event(tmp_path):

    ledger = Ledger(
        tmp_path / "orch.db"
    )

    ledger.init()


    from research_agent.models import (
        Hypothesis,
        Provenance,
    )

    hypothesis = Hypothesis(
        id="HYP-test",
        statement="test hypothesis",
        falsifier="test falsifier",
        prediction="test prediction",
        model_output_hash="test-hash",
        provenance=Provenance(
            created_by="test"
        ),
    )

    ledger.put(hypothesis)


    decision = PlannerDecision(
        action="REQUEST_MORE_EVIDENCE",
        hypothesis_id="HYP-test",
        confidence=0.5,
    )


    orch = Orchestrator(
        ledger=ledger,
        repo_commit="test"
    )


    result = orch.dispatch(
        decision,
        {
            "target": "demo"
        }
    )


    assert result is not None
