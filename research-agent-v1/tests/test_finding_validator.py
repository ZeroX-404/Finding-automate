from research_agent.finding_validator import (
    FindingValidationEngine,
)



class FakeFinding:

    file = "tests/test_auth.py"

    message = (
        "Possible hardcoded password"
    )



def test_reject_test_fixture():

    engine = FindingValidationEngine()


    result = engine.validate(
        FakeFinding()
    )


    assert (
        result.status
        ==
        "REJECTED"
    )


    assert (
        result.confidence
        >
        0.8
    )
