from research_agent.orchestrator import Orchestrator
from research_agent.state.research_state import ResearchState
from research_agent.agents.base import AgentResult


class FakeAgent:

    def execute(self, context):

        return AgentResult(
            agent_name="fake",
            status="COMPLETED",
            output={
                "confidence":0.75,
                "evidence":{
                    "supporting":2
                }
            }
        )


def test_orchestrator_state_lifecycle():

    from research_agent.state_mutation import StateMutationEngine

    state = ResearchState(
        hypothesis_id="HYP-test"
    )

    assert state.confidence == 0

    StateMutationEngine().apply_result(
        state,
        FakeAgent().execute({})
    )

    assert state.confidence == 0.75
    assert state.evidence.supporting == 2
