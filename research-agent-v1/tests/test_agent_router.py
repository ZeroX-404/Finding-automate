from research_agent.agents.router import AgentRouter
from research_agent.agents import (
    ResearcherAgent,
    CriticAgent,
)


def test_request_evidence_routes_to_researcher():

    router = AgentRouter()

    agent = router.resolve(
        "REQUEST_MORE_EVIDENCE"
    )

    assert isinstance(
        agent,
        ResearcherAgent
    )


def test_validation_routes_to_critic():

    router = AgentRouter()

    agent = router.resolve(
        "RUN_VALIDATION"
    )

    assert isinstance(
        agent,
        CriticAgent
    )


def test_unknown_action_is_blocked():

    router = AgentRouter()

    try:
        router.resolve(
            "UNKNOWN"
        )
        assert False
    except ValueError:
        assert True
