from research_agent.ledger import Ledger
from research_agent.state_models import PlannerDecisionRecord
from research_agent.decision_graph import (
    link_decision_to_state,
)
from research_agent.models import Observation, Provenance


def test_planner_decision_has_state_lineage(tmp_path):

    ledger = Ledger(
        tmp_path / "graph.db"
    )

    ledger.init()

    state_id = "STATE-test123"

    decision = PlannerDecisionRecord(
        id="DEC-test123",
        hypothesis_id="HYP-test",
        action="REQUEST_MORE_EVIDENCE",
        confidence=0.2,
    )

    ledger.put(decision)

    state = Observation(
        id=state_id,
        summary="state placeholder",
        artifact="state",
        location="runtime",
        provenance=Provenance(
            created_by="test",
            tool_name="planner-test",
            repo_commit="test",
        ),
    )

    ledger.put(state)

    link_decision_to_state(
        ledger,
        decision.id,
        state_id,
    )

    graph = ledger.graph(
        decision.id
    )

    assert len(
        graph["outgoing"]
    ) == 1

    assert (
        graph["outgoing"][0]["relation"]
        ==
        "DECIDES_ON"
    )
