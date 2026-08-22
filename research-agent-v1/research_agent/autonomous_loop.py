from __future__ import annotations


class AutonomousResearchLoop:

    def __init__(
        self,
        decision_engine,
        orchestrator,
    ):
        self.decision_engine = decision_engine
        self.orchestrator = orchestrator


    def run(
        self,
        hypothesis_id: str,
        context: dict,
        max_iterations: int = 3,
    ):

        history = []

        for step in range(max_iterations):

            decision = self.decision_engine.evaluate(
                hypothesis_id
            )

            history.append(
                decision
            )

            action = decision["action"]


            if action.value in (
                "DROP_HYPOTHESIS",
                "PROMOTE_FINDING",
            ):
                break


            result = self.orchestrator.dispatch(
                type(
                    "Decision",
                    (),
                    {
                        "action": action.value,
                        "hypothesis_id": hypothesis_id,
                    }
                )(),
                context,
            )

            history.append(
                {
                    "agent_result": result.__dict__
                }
            )


        return {
            "hypothesis_id": hypothesis_id,
            "iterations": len(history),
            "history": history,
        }
