from research_agent.research_trace import (
    ResearchTraceRecorder,
)



def test_trace_record():

    recorder = ResearchTraceRecorder()


    event = recorder.record(
        event="PROMOTE_FINDING",
        reason="high confidence",
        evidence_ids=[
            "EVD-001"
        ],
        agent_ids=[
            "ResearcherAgent"
        ],
    )


    assert (
        event.event
        ==
        "PROMOTE_FINDING"
    )



def test_trace_explain():

    recorder = ResearchTraceRecorder()


    event = recorder.record(
        "REJECT",
        "contradicting evidence",
    )


    result = recorder.explain(
        event.id
    )


    assert (
        result["decision"]
        ==
        "REJECT"
    )
