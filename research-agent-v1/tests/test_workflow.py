from research_agent.orchestrator.workflow import (
    WorkflowStatus,
    WorkflowTransition,
)


def test_valid_workflow_transition():

    wf = WorkflowTransition()

    assert wf.transition(
        WorkflowStatus.STARTED
    ) == WorkflowStatus.STARTED


    assert wf.transition(
        WorkflowStatus.RUNNING
    ) == WorkflowStatus.RUNNING


    assert wf.transition(
        WorkflowStatus.COMPLETED
    ) == WorkflowStatus.COMPLETED



def test_invalid_workflow_transition():

    wf = WorkflowTransition()

    try:
        wf.transition(
            WorkflowStatus.COMPLETED
        )
        assert False
    except ValueError:
        assert True
