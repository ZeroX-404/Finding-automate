from research_agent.agent_consensus import (
    AgentConsensusEngine,
    AgentVote,
)



def test_consensus_accept():

    engine = AgentConsensusEngine()


    result = engine.evaluate(
        [
            AgentVote(
                "researcher",
                "PROMOTE",
                0.9,
            ),

            AgentVote(
                "critic",
                "PROMOTE",
                0.8,
            ),
        ]
    )


    assert (
        result["status"]
        ==
        "ACCEPT"
    )



def test_consensus_review():

    engine = AgentConsensusEngine()


    result = engine.evaluate(
        [
            AgentVote(
                "researcher",
                "PROMOTE",
                0.6,
            ),

            AgentVote(
                "critic",
                "REJECT",
                0.5,
            ),
        ]
    )


    assert (
        result["status"]
        ==
        "REVIEW"
    )
