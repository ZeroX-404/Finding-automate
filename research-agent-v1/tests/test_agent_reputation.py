from research_agent.agent_reputation import (
    AgentReputationEngine,
)



def test_reputation_success():

    engine = AgentReputationEngine()


    engine.record_result(
        "ResearcherAgent",
        True,
    )

    engine.record_result(
        "ResearcherAgent",
        True,
    )


    assert (
        engine.score(
            "ResearcherAgent"
        )
        ==
        1.0
    )



def test_reputation_failure():

    engine = AgentReputationEngine()


    engine.record_result(
        "CriticAgent",
        False,
    )


    assert (
        engine.score(
            "CriticAgent"
        )
        ==
        0.0
    )



def test_trust_weight():

    engine = AgentReputationEngine()


    assert (
        engine.trust_weight(
            "UnknownAgent"
        )
        ==
        0.75
    )
