from research_agent.research_os import (
    AutonomousResearchOS,
)



def test_research_os_run():

    os = AutonomousResearchOS()


    result = os.run(
        target="demo-repository",
        hypothesis=
        "possible vulnerability",
    )


    assert (
        result["target"]
        ==
        "demo-repository"
    )


    assert (
        result["decision"]
        ==
        "CONTINUE"
    )
