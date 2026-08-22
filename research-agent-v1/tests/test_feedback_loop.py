from research_agent.feedback_loop import (
    AutonomousFeedbackLoop,
)


class FakeValidation:

    def __init__(self, status):

        self.status = status



def test_success_feedback():

    loop = AutonomousFeedbackLoop()


    result = loop.apply(
        FakeValidation(
            "PASS"
        )
    )


    assert (
        result.next_action
        ==
        "STRENGTHEN_HYPOTHESIS"
    )


    assert (
        result.strategy_update
        is False
    )



def test_failure_feedback():

    loop = AutonomousFeedbackLoop()


    result = loop.apply(
        FakeValidation(
            "FAIL"
        )
    )


    assert (
        result.next_action
        ==
        "REFINE_HYPOTHESIS"
    )


    assert (
        result.strategy_update
        is True
    )
