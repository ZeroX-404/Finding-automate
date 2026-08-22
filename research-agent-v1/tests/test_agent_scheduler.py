from research_agent.agent_scheduler import (
    AdaptiveAgentScheduler,
    AgentTask,
)



class FakePolicy:

    def select_agents(
        self,
        action,
    ):

        return [
            "ResearcherAgent",
            "CriticAgent",
        ]



def test_scheduler_build_plan():

    scheduler = AdaptiveAgentScheduler(
        FakePolicy()
    )


    tasks = scheduler.build_schedule(
        "REQUEST_MORE_EVIDENCE"
    )


    assert len(tasks) == 2

    assert (
        tasks[0].name
        ==
        "ResearcherAgent"
    )



def test_scheduler_execute():

    scheduler = AdaptiveAgentScheduler()


    result = scheduler.execute_plan(
        [
            AgentTask(
                "ResearcherAgent"
            )
        ],
        lambda agent:
            {
                "agent": agent
            },
    )


    assert (
        result[0]["status"]
        ==
        "COMPLETED"
    )
