from research_agent.experiment_planner import (
    AutonomousExperimentPlanner,
)



def test_create_experiment_plan():

    planner = (
        AutonomousExperimentPlanner()
    )


    plan = planner.create_plan(
        "API endpoint vulnerable"
    )


    assert (
        plan.hypothesis
        ==
        "API endpoint vulnerable"
    )


    assert (
        len(plan.steps)
        >
        0
    )


    assert (
        plan.validation_method
        ==
        "V3_DETERMINISTIC"
    )
