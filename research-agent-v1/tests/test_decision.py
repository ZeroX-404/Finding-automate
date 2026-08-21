from research_agent.state import (
    ResearchState,
    ConfidenceEngine,
    DecisionEngine,
    ResearchAction,
)


def test_promote_when_evidence_is_strong():

    state = ResearchState(
        hypothesis_id="HYP-test"
    )

    state.add_supporting_evidence(4)

    ConfidenceEngine().calculate(state)

    action = DecisionEngine().decide(state)

    assert action == ResearchAction.PROMOTE_FINDING



def test_request_more_evidence_when_critic_exists():

    state = ResearchState(
        hypothesis_id="HYP-test"
    )

    state.add_supporting_evidence(3)
    state.add_critic_objection()

    ConfidenceEngine().calculate(state)

    action = DecisionEngine().decide(state)

    assert action == ResearchAction.REQUEST_MORE_EVIDENCE



def test_drop_weak_hypothesis():

    state = ResearchState(
        hypothesis_id="HYP-test"
    )

    state.add_contradicting_evidence(3)

    ConfidenceEngine().calculate(state)

    action = DecisionEngine().decide(state)

    assert action == ResearchAction.DROP_HYPOTHESIS



def test_continue_when_uncertain():

    state = ResearchState(
        hypothesis_id="HYP-test"
    )

    state.add_supporting_evidence(1)

    ConfidenceEngine().calculate(state)

    action = DecisionEngine().decide(state)

    assert action == ResearchAction.CONTINUE_RESEARCH
