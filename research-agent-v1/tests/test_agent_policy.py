from research_agent.agent_policy import (
    AgentPolicyEngine,
)


def test_policy_select_researcher():

    policy = AgentPolicyEngine()

    agents = policy.select_agents(
        "REQUEST_MORE_EVIDENCE"
    )

    assert (
        "ResearcherAgent"
        in agents
    )


def test_policy_promotion_gate():

    policy = AgentPolicyEngine()

    assert policy.can_promote(
        0.9,
        2,
    )

    assert not policy.can_promote(
        0.5,
        2,
    )
