from research_agent.hypothesis_synthesis import (
    HypothesisSynthesisEngine,
)


class FakeEvidence:

    id = "EVD-001"

    description = (
        "Hardcoded password detected "
        "in auth.py"
    )



def test_hypothesis_generation():


    engine = (
        HypothesisSynthesisEngine()
    )


    result = engine.synthesize(
        FakeEvidence()
    )


    assert (
        "credential"
        in result.statement
    )


    assert (
        result.confidence
        ==
        0.6
    )


    assert (
        "EVD-001"
        in result.evidence_ids
    )
