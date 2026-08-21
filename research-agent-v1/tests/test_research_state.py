from research_agent.state import (
    ResearchState,
    HypothesisStatus,
)


def test_research_state_initialization():

    state = ResearchState(
        hypothesis_id="HYP-test"
    )

    assert state.hypothesis_id == "HYP-test"
    assert state.status == HypothesisStatus.ACTIVE
    assert state.confidence == 0.0


def test_research_state_tracks_evidence():

    state = ResearchState(
        hypothesis_id="HYP-test"
    )

    state.add_supporting_evidence(3)
    state.add_contradicting_evidence(1)
    state.add_neutral_evidence(2)

    assert state.evidence.supporting == 3
    assert state.evidence.contradicting == 1
    assert state.evidence.neutral == 2


def test_research_state_tracks_critic():

    state = ResearchState(
        hypothesis_id="HYP-test"
    )

    state.add_critic_objection()
    state.add_critic_objection(resolved=True)

    assert state.critic.objections == 2
    assert state.critic.resolved_objections == 1

