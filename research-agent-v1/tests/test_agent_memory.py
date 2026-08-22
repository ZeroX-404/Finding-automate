from research_agent.agent_memory import (
    AgentMemory,
)



def test_memory_store():

    memory = AgentMemory()


    memory.remember(

        fingerprint=
        "HARDCODED_SECRET:app.py",

        status=
        "REJECTED",

        confidence=
        0.9,

        reason=
        "test fixture",

    )


    result = memory.recall(
        "HARDCODED_SECRET:app.py"
    )


    assert result is not None


    assert (
        result.status
        ==
        "REJECTED"
    )


    assert (
        result.confidence
        ==
        0.9
    )
