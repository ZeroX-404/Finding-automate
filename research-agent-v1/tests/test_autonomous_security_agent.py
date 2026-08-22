from research_agent.autonomous_security_agent import (
    AutonomousSecurityResearchAgent,
)



def test_security_agent_exists():

    agent = (
        AutonomousSecurityResearchAgent()
    )


    result = agent.run(
        "./target",
        "security analysis",
    )


    assert (
        result["status"]
        ==
        "COMPLETED"
    )
