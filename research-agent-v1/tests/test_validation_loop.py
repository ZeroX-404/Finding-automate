from research_agent.validation_loop import (
    ValidationFeedbackLoop,
)


class FakeValidation:

    status = "NEEDS_REVIEW"



def test_needs_more_evidence():

    engine = ValidationFeedbackLoop()


    result = engine.decide(
        FakeValidation()
    )


    assert (
        result.action
        ==
        "COLLECT_MORE_EVIDENCE"
    )


    assert (
        result.continue_research
        is True
    )
