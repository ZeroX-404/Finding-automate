from research_agent.failure_recovery import (
    FailureRecoveryEngine,
)


def test_failure_recovery_exists():

    assert FailureRecoveryEngine is not None


def test_failure_recovery_retry():

    engine = FailureRecoveryEngine(
        max_retry=2
    )

    calls = {
        "count": 0
    }


    def failing(_):

        calls["count"] += 1

        raise RuntimeError(
            "failed"
        )


    result = engine.execute(
        failing,
        {}
    )


    assert result["status"] == "FAILED"
    assert calls["count"] == 3
