from research_agent.evidence_reasoner import (
    EvidenceReasoner,
)



def test_evidence_support():

    reasoner = EvidenceReasoner()


    reasoner.add_evidence(
        "EVD-1",
        "SUPPORTS",
        0.8,
    )


    reasoner.add_evidence(
        "EVD-2",
        "CONTRADICTS",
        0.2,
    )


    result = reasoner.evaluate()


    assert (
        result["confidence"]
        ==
        0.8
    )

    assert (
        result["evidence_count"]
        ==
        2
    )
