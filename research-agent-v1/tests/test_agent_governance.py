from research_agent.agent_governance import (
    AgentGovernanceEngine,
)



def test_governance_allow():

    engine = AgentGovernanceEngine()


    result = engine.evaluate(
        "ResearcherAgent",
        "RUN_ANALYSIS",
    )


    assert result.allowed is True



def test_governance_block():

    engine = AgentGovernanceEngine()


    result = engine.evaluate(
        "ResearcherAgent",
        "DELETE_DATA",
    )


    assert result.allowed is False

    assert (
        result.reason
        ==
        "blocked_action"
    )
