from research_agent.orchestrator.workflow import (
    WorkflowStatus,
    WorkflowTransition,
)


def test_orchestrator_workflow_full_cycle():
    wf = WorkflowTransition()

    wf.transition(WorkflowStatus.STARTED)
    wf.transition(WorkflowStatus.RUNNING)
    wf.transition(WorkflowStatus.COMPLETED)

    assert wf.current == WorkflowStatus.COMPLETED
