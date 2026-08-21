from research_agent.state import (
    ResearchState,
    ConfidenceEngine,
)


def test_confidence_increases_with_supporting_evidence():

    state = ResearchState(
        hypothesis_id="HYP-test"
    )

    state.add_supporting_evidence(3)

    score = ConfidenceEngine().calculate(state)

    assert score == 0.75


def test_confidence_decreases_with_contradiction():

    state = ResearchState(
        hypothesis_id="HYP-test"
    )

    state.add_supporting_evidence(2)
    state.add_contradicting_evidence(1)

    score = ConfidenceEngine().calculate(state)

    assert score == 0.20


def test_unresolved_critic_reduces_confidence():

    state = ResearchState(
        hypothesis_id="HYP-test"
    )

    state.add_supporting_evidence(4)
    state.add_critic_objection()

    score = ConfidenceEngine().calculate(state)

    assert score == 0.85


def test_confidence_is_bounded():

    state = ResearchState(
        hypothesis_id="HYP-test"
    )

    state.add_supporting_evidence(20)

    score = ConfidenceEngine().calculate(state)

    assert score == 1.0
