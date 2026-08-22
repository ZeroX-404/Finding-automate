from research_agent.knowledge_graph_memory import (
    KnowledgeGraphMemory,
)



def test_graph_relation():

    graph = KnowledgeGraphMemory()


    hypothesis = graph.add_node(
        "HYPOTHESIS",
        {
            "name":
            "SQL Injection"
        },
    )


    evidence = graph.add_node(
        "EVIDENCE",
        {
            "name":
            "Semgrep result"
        },
    )


    decision = graph.add_node(
        "DECISION",
        {
            "value":
            "PROMOTE"
        },
    )


    graph.connect(
        hypothesis.id,
        "SUPPORTED_BY",
        evidence.id,
    )


    graph.connect(
        evidence.id,
        "PRODUCED",
        decision.id,
    )


    result = graph.lineage(
        hypothesis.id
    )


    assert (
        evidence.id
        in result
    )


    assert (
        decision.id
        in result
    )
