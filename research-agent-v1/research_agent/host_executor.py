from __future__ import annotations

import subprocess
from dataclasses import dataclass
from uuid import uuid4


@dataclass
class ExecutionResult:

    id: str

    command: str

    status: str

    stdout: str

    stderr: str

    exit_code: int



class HostExecutor:


    def __init__(
        self,
        timeout: int = 30,
    ):

        self.timeout = timeout

        self.history = []



    def execute(
        self,
        command: str,
    ):

        try:

            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )


            execution = ExecutionResult(

                id=f"EXEC-{uuid4().hex[:12]}",

                command=command,

                status=(
                    "COMPLETED"
                    if result.returncode == 0
                    else "FAILED"
                ),

                stdout=result.stdout,

                stderr=result.stderr,

                exit_code=result.returncode,

            )


        except subprocess.TimeoutExpired as exc:

            execution = ExecutionResult(

                id=f"EXEC-{uuid4().hex[:12]}",

                command=command,

                status="TIMEOUT",

                stdout="",

                stderr=str(exc),

                exit_code=-1,

            )


        self.history.append(
            execution
        )


        return execution
