from research_agent.state_mutation import (
    StateMutationEngine,
)

from research_agent.state.research_state import (
    ResearchState,
)

from research_agent.agents.base import (
    AgentResult,
)


def test_state_mutation_updates_snapshot():

    state = ResearchState(
        hypothesis_id="HYP-test"
    )


    result = AgentResult(
        agent_name="ResearcherAgent",
        status="COMPLETED",
        output={
            "confidence":0.75,
            "next_action":"RUN_VALIDATION",
            "evidence":{
                "supporting":2
            }
        }
    )


    engine = StateMutationEngine()

    snapshot = engine.apply_result(
        state,
        result
    )


    assert snapshot.confidence == 0.75
    assert snapshot.next_action == "RUN_VALIDATION"
    assert snapshot.evidence["supporting"] == 2
