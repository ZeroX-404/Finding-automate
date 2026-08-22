from research_agent.state_transition import (
    StateTransitionEngine,
)

from research_agent.models import (
    Finding,
    Provenance,
    ResearchState,
)

from research_agent.state.decision import (
    ResearchAction,
)



def test_request_evidence_moves_candidate_to_under_test():

    finding = Finding(
        id="FIND-test",
        title="test",
        description="test",
        state=ResearchState.CANDIDATE,
        provenance=Provenance(
            created_by="test"
        ),
    )


    engine = StateTransitionEngine()


    result = engine.apply(
        finding,
        ResearchAction.REQUEST_MORE_EVIDENCE,
    )


    assert result.state == ResearchState.UNDER_TEST



def test_continue_research_keeps_state():

    finding = Finding(
        id="FIND-test",
        title="test",
        description="test",
        state=ResearchState.CANDIDATE,
        provenance=Provenance(
            created_by="test"
        ),
    )


    result = StateTransitionEngine().apply(
        finding,
        ResearchAction.CONTINUE_RESEARCH,
    )


    assert result.state == ResearchState.CANDIDATE
