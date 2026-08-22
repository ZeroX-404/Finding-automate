from __future__ import annotations


class FailureRecoveryEngine:

    def __init__(
        self,
        max_retry: int = 2,
    ):
        self.max_retry = max_retry


    def execute(
        self,
        executor,
        context: dict,
    ):

        errors = []

        for attempt in range(
            self.max_retry + 1
        ):

            try:

                result = executor(
                    context
                )

                return {
                    "status": "SUCCESS",
                    "attempt": attempt + 1,
                    "result": result,
                    "errors": errors,
                }


            except Exception as exc:

                errors.append(
                    str(exc)
                )


        return {
            "status": "FAILED",
            "attempt": self.max_retry + 1,
            "result": None,
            "errors": errors,
        }
