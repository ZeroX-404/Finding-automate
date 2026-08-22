from research_agent.self_calibration import (
    SelfCalibrationEngine,
)



def test_agent_reliability_update():

    engine = SelfCalibrationEngine()


    engine.update(
        "ResearcherAgent",
        True,
    )


    engine.update(
        "ResearcherAgent",
        True,
    )


    assert (
        engine.weight(
            "ResearcherAgent"
        )
        ==
        1.0
    )



def test_confidence_calibration():

    engine = SelfCalibrationEngine()


    value = engine.calibrate_confidence(
        0.9,
        [
            "ResearcherAgent"
        ],
    )


    assert value == 0.45
