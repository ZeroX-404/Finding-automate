from research_agent.runtime_telemetry import (
    RuntimeTelemetry,
)


def test_runtime_telemetry():

    telemetry = RuntimeTelemetry()

    telemetry.record(
        "START",
        {
            "component": "runtime"
        }
    )

    telemetry.complete()


    assert telemetry.status == "COMPLETED"

    assert len(
        telemetry.events
    ) == 1
