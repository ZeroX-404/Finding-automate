from research_agent.host_executor import (
    HostExecutor,
)



def test_execute_command():

    executor = HostExecutor()


    result = executor.execute(
        "echo hello"
    )


    assert (
        result.status
        ==
        "COMPLETED"
    )


    assert (
        "hello"
        in result.stdout
    )



def test_failed_command():

    executor = HostExecutor()


    result = executor.execute(
        "command_that_does_not_exist"
    )


    assert (
        result.status
        ==
        "FAILED"
    )
