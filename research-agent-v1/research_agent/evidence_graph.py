from __future__ import annotations

from .models import EdgeRelation


def attach_evidence(
    ledger,
    producer_id: str,
    evidence_id: str,
):
    """
    Bind workflow output to evidence object.

    producer_id:
        Workflow / Agent / Experiment object

    evidence_id:
        Evidence object
    """

    ledger.add_edge(
        producer_id,
        EdgeRelation.PRODUCES,
        evidence_id,
    )


def attach_claim_support(
    ledger,
    evidence_id: str,
    claim_id: str,
):
    """
    Evidence supports a claim.
    """

    ledger.add_edge(
        evidence_id,
        EdgeRelation.SUPPORTS,
        claim_id,
    )


def attach_claim_contradiction(
    ledger,
    evidence_id: str,
    claim_id: str,
):
    """
    Evidence contradicts a claim.
    """

    ledger.add_edge(
        evidence_id,
        EdgeRelation.CONTRADICTS,
        claim_id,
    )
