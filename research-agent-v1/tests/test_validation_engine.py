from research_agent.validation_engine import (
    AutonomousValidationEngine,
)



def test_validation_pass():

    engine = AutonomousValidationEngine()


    result = engine.validate(
        {
            "success": True
        }
    )


    assert (
        result.status
        ==
        "PASS"
    )


    assert (
        result.confidence_delta
        ==
        0.2
    )



def test_confidence_update():

    engine = AutonomousValidationEngine()


    validation = engine.validate(
        {
            "success": True
        }
    )


    confidence = (
        engine.confidence_update(
            0.5,
            validation,
        )
    )


    assert (
        confidence
        ==
        0.7
    )
