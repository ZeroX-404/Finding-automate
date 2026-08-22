from __future__ import annotations


class AutonomousRuntime:

    def __init__(
        self,
        loop,
        recovery,
    ):
        self.loop = loop
        self.recovery = recovery


    def run(
        self,
        hypothesis_id: str,
        context: dict,
    ):

        result = self.recovery.execute(
            lambda _: self.loop.run(
                hypothesis_id,
                context,
            ),
            context,
        )

        return result
