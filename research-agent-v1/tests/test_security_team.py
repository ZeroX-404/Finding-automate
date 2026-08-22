from research_agent.security_team import (
    ScoutAgent,
    CriticAgent,
    ValidatorAgent,
    LeadResearcherAgent,
)



class FakeFinding:

    file = "app.py"



def test_security_team():

    finding = FakeFinding()


    messages = [

        ScoutAgent()
        .analyze(finding),

        CriticAgent()
        .analyze(finding),

        ValidatorAgent()
        .analyze(finding),

    ]


    result = (
        LeadResearcherAgent()
        .decide(messages)
    )


    assert (
        len(result.messages)
        ==
        3
    )


    assert (
        result.decision
        ==
        "NEEDS_VALIDATION"
    )
