from __future__ import annotations

from uuid import uuid4

from research_agent.agents import (
    ResearcherAgent,
    CriticAgent,
)

from research_agent.agents.router import AgentRouter

from research_agent.models import (
    OrchestratorEvent,
    OrchestratorStatus,
    Provenance,
    EdgeRelation,
    AgentSelectionEvent,
)


class Orchestrator:

    def __init__(
        self,
        ledger=None,
        repo_commit: str | None = None,
    ):

        self.ledger = ledger
        self.repo_commit = repo_commit

        self.router = AgentRouter()


    def dispatch(
        self,
        decision,
        context: dict,
    ):

        decision_id = f"DEC-{uuid4().hex[:12]}"

        agent = self.router.resolve(
            decision.action
        )


        selection_event = None

        if self.ledger:

            selection_event = AgentSelectionEvent(
                decision_id=decision_id,
                action=decision.action,
                selected_agent=agent.__class__.__name__,
                provenance=Provenance(
                    created_by="orchestrator",
                    repo_commit=self.repo_commit,
                )
            )

            self.ledger.put(
                selection_event
            )


        event = None

        if self.ledger:

            event = OrchestratorEvent(
                decision_id=decision_id,
                agent_name=agent.__class__.__name__,
                status=OrchestratorStatus.RUNNING,
                input_payload=context,
                provenance=Provenance(
                    created_by="orchestrator",
                    repo_commit=self.repo_commit,
                )
            )

            self.ledger.put(event)

            if selection_event:
                self.ledger.add_edge(
                    selection_event.id,
                    EdgeRelation.ROUTES_TO,
                    event.id,
                )

            if decision.hypothesis_id:
                self.ledger.add_edge(
                    event.id,
                    EdgeRelation.DECIDES_ON,
                    decision.hypothesis_id,
                )


        try:

            result = agent.execute(
                context
            )

            if event and self.ledger:

                completed = OrchestratorEvent(
                    id=event.id,
                    decision_id=decision_id,
                    agent_name=agent.__class__.__name__,
                    status=OrchestratorStatus.COMPLETED,
                    input_payload=context,
                    output_payload=result.__dict__,
                    provenance=event.provenance,
                )

                self.ledger.put(completed)


            return result


        except Exception as exc:

            if event and self.ledger:

                failed = OrchestratorEvent(
                    id=event.id,
                    decision_id=decision_id,
                    agent_name=agent.__class__.__name__,
                    status=OrchestratorStatus.FAILED,
                    input_payload=context,
                    error=str(exc),
                    provenance=event.provenance,
                )

                self.ledger.put(failed)

            raise
