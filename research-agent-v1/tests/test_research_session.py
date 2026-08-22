from research_agent.research_session import (
    ResearchSession,
)



def test_session_record():

    session = ResearchSession()


    session.record(
        "EVIDENCE_CREATED",
        {
            "id":
            "EVD-001"
        }
    )


    result = session.export()


    assert (
        result["session_id"]
        .startswith("RUN-")
    )


    assert (
        len(result["events"])
        ==
        1
    )


    assert (
        result["events"][0]["name"]
        ==
        "EVIDENCE_CREATED"
    )
