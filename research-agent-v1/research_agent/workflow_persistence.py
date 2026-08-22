from __future__ import annotations

from .models import (
    WorkflowRun,
    Provenance,
    EdgeRelation,
)


class WorkflowPersistence:

    def __init__(
        self,
        ledger,
        repo_commit=None,
    ):
        self.ledger = ledger
        self.repo_commit = repo_commit


    def start(
        self,
        decision,
        agent_name,
    ):

        workflow = WorkflowRun(
            decision_id=getattr(
                decision,
                "id",
                "DEC-unknown",
            ),

            agent_name=agent_name,

            provenance=Provenance(
                created_by="workflow-persistence",
                repo_commit=self.repo_commit,
            )
        )

        self.ledger.put(
            workflow
        )

        return workflow


    def bind(
        self,
        workflow_id,
        object_id,
    ):

        self.ledger.add_edge(
            workflow_id,
            EdgeRelation.WORKFLOW_OF,
            object_id,
        )
