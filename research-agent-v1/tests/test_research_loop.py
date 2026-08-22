from research_agent.research_loop import (
    ResearchLoopController,
)



def test_research_loop_confirmation():

    loop = ResearchLoopController()


    result = loop.run(
        "HYP-001",
        max_iterations=5,
    )


    assert (
        result.state
        ==
        "CONFIRMED"
    )


    assert (
        result.confidence
        >=
        0.8
    )



def test_research_loop_limit():

    loop = ResearchLoopController()


    result = loop.run(
        "HYP-002",
        max_iterations=2,
    )


    assert (
        result.iterations
        ==
        2
    )
