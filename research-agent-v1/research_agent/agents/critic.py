from .base import BaseAgent, AgentResult


class CriticAgent(BaseAgent):

    name = "critic"


    def execute(self, context: dict):

        return AgentResult(
            agent_name=self.name,
            status="COMPLETED",
            output={
                "action":
                    "REVIEW_EVIDENCE",

                "hypothesis_id":
                    context.get(
                        "hypothesis_id"
                    )
            },
        )
