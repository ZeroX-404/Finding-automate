from research_agent.ledger import Ledger
from research_agent.evidence_graph import (
    attach_evidence,
    attach_claim_support,
    attach_claim_contradiction,
)

from research_agent.models import (
    Evidence,
    Claim,
    EvidenceRelation,
    ClaimState,
    Provenance,
)


def test_evidence_graph_lineage(tmp_path):

    ledger = Ledger(
        tmp_path / "graph.db"
    )

    ledger.init()


    evidence = Evidence(
        description="static analysis result",
        source_type="TOOL_OUTPUT",
        source_ref="semgrep.json",
        relation=EvidenceRelation.SUPPORTS,
        provenance=Provenance(
            created_by="test"
        ),
    )


    claim = Claim(
        statement="issue is exploitable",
        state=ClaimState.CANDIDATE,
        provenance=Provenance(
            created_by="test"
        ),
    )


    ledger.put(evidence)
    ledger.put(claim)


    workflow_id = "WORK-test"

    from research_agent.models import OrchestratorEvent, OrchestratorStatus

    workflow = OrchestratorEvent(
        decision_id="DEC-test",
        agent_name="researcher",
        status=OrchestratorStatus.COMPLETED,
        provenance=Provenance(
            created_by="test"
        ),
    )

    ledger.put(workflow)


    attach_evidence(
        ledger,
        workflow.id,
        evidence.id,
    )


    attach_claim_support(
        ledger,
        evidence.id,
        claim.id,
    )


    rows = ledger.export_graph()


    assert len(rows["edges"]) >= 2
