from __future__ import annotations


from dataclasses import dataclass, field



@dataclass
class AgentTask:

    name: str

    priority: int = 0

    status: str = "PENDING"

    metadata: dict = field(
        default_factory=dict
    )



class AdaptiveAgentScheduler:


    def __init__(
        self,
        policy_engine=None,
    ):

        self.policy_engine = policy_engine



    def build_schedule(
        self,
        action: str,
    ) -> list[AgentTask]:


        if self.policy_engine:

            agents = (
                self.policy_engine
                .select_agents(action)
            )

        else:

            agents = []


        tasks = []

        for index, agent in enumerate(
            agents
        ):

            tasks.append(
                AgentTask(
                    name=agent,
                    priority=index,
                )
            )


        return sorted(
            tasks,
            key=lambda x:
                x.priority,
        )



    def execute_plan(
        self,
        tasks,
        executor,
    ):

        results = []


        for task in tasks:

            try:

                result = executor(
                    task.name
                )

                task.status = (
                    "COMPLETED"
                )

                results.append(
                    {
                        "agent":
                            task.name,
                        "status":
                            task.status,
                        "result":
                            result,
                    }
                )


            except Exception as exc:

                task.status = (
                    "FAILED"
                )

                results.append(
                    {
                        "agent":
                            task.name,
                        "status":
                            task.status,
                        "error":
                            str(exc),
                    }
                )


        return results
