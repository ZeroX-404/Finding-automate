from research_agent.case_learning import (
    AutonomousCaseLearner,
)



def test_case_learning():

    learner = AutonomousCaseLearner()


    learner.learn(
        [
            "api",
            "sql",
        ],
        "SUCCESS",
        0.9,
    )


    assert (
        len(
            learner.successful_cases()
        )
        ==
        1
    )



def test_learning_stats():

    learner = AutonomousCaseLearner()


    learner.learn(
        [
            "x"
        ],
        "SUCCESS",
        0.8,
    )


    learner.learn(
        [
            "y"
        ],
        "FAILURE",
        0.2,
    )


    result = learner.stats()


    assert (
        result["total"]
        ==
        2
    )


    assert (
        result["success_rate"]
        ==
        0.5
    )
