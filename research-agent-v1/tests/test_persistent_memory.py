from research_agent.persistent_memory import (
    PersistentMemory,
)



def test_memory_persistence(
    tmp_path,
):

    db = tmp_path / "memory.db"


    memory = PersistentMemory(
        db
    )


    memory.store(
        "decision",
        {
            "decision":
            "PROMOTE"
        },
    )


    result = memory.query(
        "decision"
    )


    assert len(result) == 1


    assert (
        result[0]["decision"]
        ==
        "PROMOTE"
    )



def test_memory_count(
    tmp_path,
):

    memory = PersistentMemory(
        tmp_path / "memory.db"
    )


    assert (
        memory.count()
        ==
        0
    )
