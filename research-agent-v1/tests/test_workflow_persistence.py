from research_agent.ledger import Ledger
from research_agent.workflow_persistence import (
    WorkflowPersistence,
)

from research_agent.planner.models import (
    PlannerDecision,
)



def test_workflow_persistence(tmp_path):

    ledger = Ledger(
        tmp_path / "workflow.db"
    )

    ledger.init()


    decision = PlannerDecision(
        action="REQUEST_MORE_EVIDENCE"
    )


    store = WorkflowPersistence(
        ledger
    )


    workflow = store.start(
        decision,
        "ResearcherAgent"
    )


    assert workflow.agent_name == "ResearcherAgent"

    assert ledger.get(
        workflow.id
    ) is not None
