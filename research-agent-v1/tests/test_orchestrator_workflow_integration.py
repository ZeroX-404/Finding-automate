from research_agent.orchestrator.workflow import (
    WorkflowStatus,
    WorkflowTransition,
)


def test_workflow_reaches_completed():

    workflow = WorkflowTransition()

    workflow.transition(
        WorkflowStatus.STARTED
    )

    workflow.transition(
        WorkflowStatus.RUNNING
    )

    workflow.transition(
        WorkflowStatus.COMPLETED
    )

    assert workflow.current == WorkflowStatus.COMPLETED
