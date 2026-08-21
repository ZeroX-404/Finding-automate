from .base import BaseAgent, AgentResult


class ResearcherAgent(BaseAgent):

    name = "researcher"


    def execute(self, context: dict):

        return AgentResult(
            agent_name=self.name,
            status="COMPLETED",
            output={
                "action":
                    "COLLECT_EVIDENCE",

                "hypothesis_id":
                    context.get(
                        "hypothesis_id"
                    )
            },
        )
