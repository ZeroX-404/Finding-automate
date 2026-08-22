from research_agent.hypothesis_evolution import (
    HypothesisEvolutionEngine,
)



def test_hypothesis_strengthened():

    engine = HypothesisEvolutionEngine()


    revision = engine.evolve(
        "HYP-001",
        {
            "confidence": 0.9
        },
    )


    assert (
        revision.reason
        ==
        "SUPPORTING_EVIDENCE"
    )



def test_hypothesis_lineage():

    engine = HypothesisEvolutionEngine()


    engine.create_revision(
        "HYP-001",
        "new hypothesis",
        0.5,
        "TEST",
    )


    history = engine.lineage(
        "HYP-001"
    )


    assert len(history) == 1
