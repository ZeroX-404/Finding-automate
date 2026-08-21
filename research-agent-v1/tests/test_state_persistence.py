from research_agent.ledger import Ledger
from research_agent.state import ResearchState
from research_agent.state_persistence import snapshot_from_state


def test_research_state_snapshot_saved_in_ledger(tmp_path):

    ledger = Ledger(
        tmp_path / "state.db"
    )

    ledger.init()

    state = ResearchState(
        hypothesis_id="HYP-test"
    )

    state.add_supporting_evidence(3)
    state.confidence = 0.75

    snapshot = snapshot_from_state(state)

    object_id = ledger.put(snapshot)

    result = ledger.get(object_id)

    assert result is not None

    assert result["kind"] == "ResearchStateSnapshot"

    assert result["payload"]["confidence"] == 0.75
