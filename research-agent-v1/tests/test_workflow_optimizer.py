from research_agent.workflow_optimizer import (
    AutonomousWorkflowOptimizer,
    WorkflowPlan,
)



def test_choose_best_workflow():

    optimizer = (
        AutonomousWorkflowOptimizer()
    )


    workflow_a = WorkflowPlan(
        name="A",
        agents=[
            "Researcher",
            "Critic",
        ],
        success_rate=0.8,
        execution_time=20,
    )


    workflow_b = WorkflowPlan(
        name="B",
        agents=[
            "Researcher",
            "Validator",
            "Critic",
        ],
        success_rate=0.95,
        execution_time=10,
    )


    result = optimizer.optimize(
        [
            workflow_a,
            workflow_b,
        ]
    )


    assert (
        result.name
        ==
        "B"
    )
