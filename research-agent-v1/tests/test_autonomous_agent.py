from research_agent.autonomous_agent import (
    AutonomousResearchAgent,
)

from research_agent.validation_engine import (
    AutonomousValidationEngine,
)

from research_agent.research_supervisor import (
    AutonomousResearchSupervisor,
)



def test_autonomous_agent_run():

    agent = AutonomousResearchAgent(

        validator=
        AutonomousValidationEngine(),

        supervisor=
        AutonomousResearchSupervisor(),

    )


    result = agent.run(
        target="demo",
        hypothesis=
        "possible vulnerability",
    )


    assert (
        result["status"]
        ==
        "COMPLETED"
    )


    assert (
        result["iterations"]
        >
        0
    )
