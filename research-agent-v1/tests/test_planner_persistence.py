from research_agent.ledger import Ledger
from research_agent.state import ResearchState
from research_agent.planner import ResearchPlanner
from research_agent.planner_persistence import decision_to_record


def test_planner_decision_saved_in_ledger(tmp_path):

    ledger = Ledger(
        tmp_path / "decision.db"
    )

    ledger.init()


    state = ResearchState(
        hypothesis_id="HYP-planner-test"
    )

    state.confidence = 0.2


    decision = (
        ResearchPlanner()
        .decide(state)
    )


    record = decision_to_record(
        decision
    )


    object_id = ledger.put(
        record
    )


    saved = ledger.get(
        object_id
    )


    assert saved is not None

    assert (
        saved["kind"]
        ==
        "PlannerDecisionRecord"
    )

    assert (
        saved["payload"]["action"]
        ==
        "REQUEST_MORE_EVIDENCE"
    )
