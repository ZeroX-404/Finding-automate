from research_agent.models import (
    OrchestratorEvent,
    OrchestratorStatus,
    Provenance,
)


def test_orchestrator_event_model():

    event = OrchestratorEvent(
        decision_id="DEC-test",
        agent_name="researcher",
        status=OrchestratorStatus.COMPLETED,
        input_payload={
            "hypothesis_id":"HYP-test"
        },
        output_payload={
            "action":"REQUEST_EVIDENCE"
        },
        provenance=Provenance(
            created_by="orchestrator-test"
        )
    )

    assert event.status == OrchestratorStatus.COMPLETED
    assert event.orchestrator_version == "2.2.2"
