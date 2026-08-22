from research_agent.semantic_retrieval import (
    SemanticResearchRetrieval,
)



def test_retrieve_similar_case():

    engine = SemanticResearchRetrieval()


    engine.add_case(
        "CASE-001",
        [
            "api",
            "sql",
            "input",
        ],
        "PROMOTE",
    )


    engine.add_case(
        "CASE-002",
        [
            "auth",
            "token",
        ],
        "REJECT",
    )


    result = engine.retrieve(
        [
            "api",
            "sql",
        ]
    )


    assert (
        result[0]["case_id"]
        ==
        "CASE-001"
    )


    assert (
        result[0]["score"]
        >
        0
    )
