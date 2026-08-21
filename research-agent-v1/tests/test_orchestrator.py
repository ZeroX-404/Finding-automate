from research_agent.state import ResearchState
from research_agent.planner import ResearchPlanner
from research_agent.orchestrator import Orchestrator


def test_orchestrator_routes_low_confidence_to_researcher():

    state = ResearchState(
        hypothesis_id="HYP-001"
    )

    state.confidence = 0.2


    decision = (
        ResearchPlanner()
        .decide(state)
    )


    result = (
        Orchestrator()
        .dispatch(
            decision,
            {
                "hypothesis_id":
                    state.hypothesis_id
            },
        )
    )


    assert result.agent_name == "researcher"

    assert result.status == "COMPLETED"



def test_orchestrator_routes_validation_to_critic():

    state = ResearchState(
        hypothesis_id="HYP-002"
    )

    state.confidence = 0.7

    state.add_critic_objection()


    decision = (
        ResearchPlanner()
        .decide(state)
    )


    result = (
        Orchestrator()
        .dispatch(
            decision,
            {
                "hypothesis_id":
                    state.hypothesis_id
            },
        )
    )


    assert result.agent_name == "critic"
