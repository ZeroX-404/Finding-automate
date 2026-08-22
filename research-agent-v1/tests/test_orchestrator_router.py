from research_agent.orchestrator import Orchestrator
from research_agent.planner.models import PlannerDecision


def test_orchestrator_uses_router():

    orch = Orchestrator()

    decision = PlannerDecision(
        action="REQUEST_MORE_EVIDENCE",
        hypothesis_id="HYP-test",
        confidence=0.5,
    )

    agent = orch.router.resolve(
        decision.action
    )

    assert agent.name == "researcher"
