from research_agent.human_oversight import (
    HumanOversightGateway,
)



def test_create_approval_request():

    gateway = HumanOversightGateway()


    request = gateway.request(
        "ResearcherAgent",
        "EXECUTE_CODE",
    )


    assert (
        request.status
        ==
        "PENDING"
    )



def test_approve_request():

    gateway = HumanOversightGateway()


    request = gateway.request(
        "ResearcherAgent",
        "EXECUTE_CODE",
    )


    result = gateway.approve(
        request.id,
        "security-reviewer",
        "approved after review",
    )


    assert (
        result.status
        ==
        "APPROVED"
    )

    assert (
        result.reviewer
        ==
        "security-reviewer"
    )
