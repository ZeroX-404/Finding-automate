from research_agent.distributed_runtime import (
    DistributedAgentRuntime,
)



def test_worker_registration():

    runtime = DistributedAgentRuntime()


    worker = runtime.register_worker(
        "Researcher-01",
        [
            "STATIC_ANALYSIS"
        ],
    )


    assert (
        worker.name
        ==
        "Researcher-01"
    )



def test_task_lifecycle():

    runtime = DistributedAgentRuntime()


    task = runtime.submit(
        "ResearcherAgent",
        {
            "target":
            "repo"
        },
    )


    runtime.dispatch(
        task.id
    )


    result = runtime.complete(
        task.id
    )


    assert (
        result.status
        ==
        "COMPLETED"
    )
