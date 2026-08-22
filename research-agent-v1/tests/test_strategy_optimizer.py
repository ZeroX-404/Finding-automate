from research_agent.strategy_optimizer import (
    SelfImprovingStrategyEngine,
    ResearchStrategy,
)



def test_strategy_improvement():

    engine = (
        SelfImprovingStrategyEngine()
    )


    old = ResearchStrategy(
        name="OLD",
        steps=[
            "SCAN",
            "REVIEW",
        ],
        success_rate=0.6,
        usage_count=10,
    )


    improved = ResearchStrategy(
        name="IMPROVED",
        steps=[
            "PARSER",
            "SCAN",
            "VALIDATE",
        ],
        success_rate=0.9,
        usage_count=10,
    )


    result = engine.recommend(
        [
            old,
            improved,
        ]
    )


    assert (
        result["strategy"]
        ==
        "IMPROVED"
    )


    assert (
        result["confidence"]
        ==
        0.9
    )
