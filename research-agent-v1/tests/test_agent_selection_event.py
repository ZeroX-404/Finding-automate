from research_agent.models import (
    AgentSelectionEvent,
    Provenance,
)


def test_agent_selection_event():

    event = AgentSelectionEvent(
        decision_id="DEC-test",
        action="REQUEST_MORE_EVIDENCE",
        selected_agent="ResearcherAgent",
        provenance=Provenance(
            created_by="test"
        )
    )

    assert event.selected_agent == "ResearcherAgent"
    assert event.action == "REQUEST_MORE_EVIDENCE"
