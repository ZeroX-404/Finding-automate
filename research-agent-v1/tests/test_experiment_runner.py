from research_agent.experiment_runner import (
    AutonomousExperimentRunner,
)



class FakeHypothesis:

    statement = (
        "Possible hardcoded credential exposure"
    )



def test_experiment_creation():

    runner = (
        AutonomousExperimentRunner()
    )


    result = runner.run(
        FakeHypothesis()
    )


    assert (
        result.status
        ==
        "COMPLETED"
    )


    assert (
        len(result.observations)
        >=
        3
    )


    assert (
        "Locate credential usage"
        in
        result.observations
    )
