from research_agent.agent_execution_graph import (
    MultiAgentExecutionGraph,
)


def test_execution_graph_order():

    graph = MultiAgentExecutionGraph()


    graph.add_agent(
        "Researcher"
    )

    graph.add_agent(
        "Critic",
        [
            "Researcher"
        ],
    )


    order = graph.execution_order()


    assert order == [
        "Researcher",
        "Critic",
    ]



def test_execution_graph_run():

    graph = MultiAgentExecutionGraph()

    graph.add_agent(
        "Researcher"
    )


    result = graph.run(
        lambda name:
            {
                "agent": name
            }
    )


    assert (
        result["Researcher"]["agent"]
        ==
        "Researcher"
    )
