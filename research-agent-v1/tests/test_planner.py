from research_agent.state import ResearchState
from research_agent.planner import ResearchPlanner


def test_low_confidence_requests_evidence():

    state = ResearchState(
        hypothesis_id="HYP-1"
    )

    state.confidence = 0.2


    result = ResearchPlanner().decide(state)


    assert result.action == "REQUEST_MORE_EVIDENCE"



def test_unresolved_critic_runs_validation():

    state = ResearchState(
        hypothesis_id="HYP-2"
    )

    state.confidence = 0.7
    state.add_critic_objection()


    result = ResearchPlanner().decide(state)


    assert result.action == "RUN_VALIDATION"



def test_high_confidence_promotes():

    state = ResearchState(
        hypothesis_id="HYP-3"
    )

    state.confidence = 0.95


    result = ResearchPlanner().decide(state)


    assert result.action == "PROMOTE_FINDING"
