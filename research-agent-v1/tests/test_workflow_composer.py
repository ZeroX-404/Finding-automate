from research_agent.workflow_composer import (
    ResearchWorkflowComposer,
)


class FakeProposal:

    id = "PRP-001"

    method = "REPRODUCTION"



def test_compose_workflow():

    composer = (
        ResearchWorkflowComposer()
    )


    result = composer.compose(
        FakeProposal()
    )


    assert (
        result.proposal_id
        ==
        "PRP-001"
    )


    assert (
        len(result.steps)
        >=
        5
    )


    assert (
        "Validate security impact"
        in
        result.steps
    )
