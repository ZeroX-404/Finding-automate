from research_agent.knowledge_graph import (
    PersistentKnowledgeGraph,
)



def test_graph_persistence(
    tmp_path,
):

    graph = PersistentKnowledgeGraph(
        tmp_path / "graph.json"
    )


    graph.add_node(
        "EVD-001",
        "evidence",
        {
            "file":
            "app.py"
        }
    )


    graph.add_node(
        "HYP-001",
        "hypothesis",
        {}
    )


    graph.add_edge(
        "EVD-001",
        "supports",
        "HYP-001",
    )


    graph2 = PersistentKnowledgeGraph(
        tmp_path / "graph.json"
    )


    assert (
        graph2.find_node(
            "EVD-001"
        )
        is not None
    )


    assert (
        len(graph2.edges)
        ==
        1
    )
