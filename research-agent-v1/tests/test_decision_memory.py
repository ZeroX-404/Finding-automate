from research_agent.decision_memory import (
    DecisionMemory,
    DecisionRecord,
)



def test_memory_store():

    memory = DecisionMemory()


    record = memory.store(
        DecisionRecord(
            decision="PROMOTE",
            confidence=0.9,
            agents=[
                "ResearcherAgent"
            ],
        )
    )


    result = memory.find_similar(
        "PROMOTE"
    )


    assert len(result) == 1

    assert result[0].id == record.id



def test_memory_accuracy():

    memory = DecisionMemory()


    record = memory.store(
        DecisionRecord(
            decision="PROMOTE",
            agents=[
                "ResearcherAgent"
            ],
        )
    )


    memory.update_outcome(
        record.id,
        "SUCCESS",
    )


    assert (
        memory.agent_accuracy(
            "ResearcherAgent"
        )
        ==
        1.0
    )
