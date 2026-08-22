from __future__ import annotations

from research_agent.runtime_telemetry import (
    RuntimeTelemetry,
)


class ResearchAgentRuntime:

    def __init__(
        self,
        autonomous_loop,
        recovery_engine,
    ):

        self.loop = autonomous_loop
        self.recovery = recovery_engine


    def run(
        self,
        hypothesis_id: str,
        context: dict,
    ):

        telemetry = RuntimeTelemetry()

        telemetry.record(
            "RUNTIME_START",
            {
                "hypothesis_id": hypothesis_id
            }
        )


        try:

            result = self.recovery.execute(
                lambda _: self.loop.run(
                    hypothesis_id,
                    context,
                ),
                context,
            )


            telemetry.record(
                "RUNTIME_RESULT",
                {
                    "status":
                        result.get("status")
                }
            )


            telemetry.complete()


            return {
                "run_id": telemetry.run_id,
                "status": telemetry.status,
                "result": result,
                "telemetry": {
                    "events":
                        telemetry.events,
                    "started_at":
                        telemetry.started_at,
                    "finished_at":
                        telemetry.finished_at,
                }
            }


        except Exception as exc:

            telemetry.fail(
                str(exc)
            )

            return {
                "run_id": telemetry.run_id,
                "status": telemetry.status,
                "error": str(exc),
                "telemetry": {
                    "events":
                        telemetry.events
                }
            }
