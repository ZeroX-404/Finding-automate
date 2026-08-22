from research_agent.research_supervisor import (
    AutonomousResearchSupervisor,
)



def test_stop_high_confidence():

    supervisor = (
        AutonomousResearchSupervisor()
    )


    result = supervisor.evaluate(
        confidence=0.9,
        iteration=2,
    )


    assert (
        result.action
        ==
        "STOP"
    )



def test_continue_research():

    supervisor = (
        AutonomousResearchSupervisor()
    )


    result = supervisor.evaluate(
        confidence=0.5,
        iteration=2,
    )


    assert (
        result.action
        ==
        "CONTINUE"
    )



def test_refine_low_confidence():

    supervisor = (
        AutonomousResearchSupervisor()
    )


    result = supervisor.evaluate(
        confidence=0.1,
        iteration=1,
    )


    assert (
        result.action
        ==
        "REFINE_HYPOTHESIS"
    )
