from research_agent.strategy_planner import (
    AutonomousStrategyPlanner,
)



def test_strategy_selection():

    planner = AutonomousStrategyPlanner()


    strategy = planner.select_strategy(
        "find vulnerability"
    )


    assert (
        strategy.name
        ==
        "STATIC_ANALYSIS"
    )


    assert (
        "ResearcherAgent"
        in strategy.required_agents
    )
