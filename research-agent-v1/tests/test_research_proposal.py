from research_agent.research_proposal import (
    ResearchProposalGenerator,
)


class FakeHypothesis:

    id = "HYP-001"

    statement = (
        "Possible hardcoded credential "
        "exposure in source code"
    )



def test_generate_proposal():

    generator = (
        ResearchProposalGenerator()
    )


    result = generator.generate(
        FakeHypothesis()
    )


    assert (
        result.method
        ==
        "REPRODUCTION"
    )


    assert (
        len(
            result.requested_evidence
        )
        >
        0
    )


    assert (
        result.hypothesis_id
        ==
        "HYP-001"
    )
