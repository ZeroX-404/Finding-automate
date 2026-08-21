from research_agent.state import ResearchState
from research_agent.state_snapshot import create_state_snapshot


def test_state_snapshot_contains_research_memory():

    state = ResearchState(
        hypothesis_id="HYP-test"
    )

    state.add_supporting_evidence(3)
    state.add_critic_objection()

    snapshot = create_state_snapshot(
        state,
        parent_ids=["EVD-test"]
    )

    assert snapshot["kind"] == "ResearchStateSnapshot"

    assert snapshot["hypothesis_id"] == "HYP-test"

    assert snapshot["evidence"]["supporting"] == 3

    assert snapshot["critic"]["objections"] == 1

    assert snapshot["parent_ids"] == [
        "EVD-test"
    ]
