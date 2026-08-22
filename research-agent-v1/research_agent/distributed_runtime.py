from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4



@dataclass
class AgentTask:

    id: str = field(
        default_factory=lambda:
        f"TASK-{uuid4().hex[:12]}"
    )

    agent: str = ""

    payload: dict = field(
        default_factory=dict
    )

    status: str = "PENDING"



@dataclass
class Worker:

    name: str

    capabilities: list[str]



class DistributedAgentRuntime:


    def __init__(self):

        self.workers = []

        self.tasks = []



    def register_worker(
        self,
        name: str,
        capabilities: list[str],
    ):

        worker = Worker(
            name=name,
            capabilities=capabilities,
        )

        self.workers.append(
            worker
        )

        return worker



    def submit(
        self,
        agent: str,
        payload: dict,
    ):

        task = AgentTask(
            agent=agent,
            payload=payload,
        )

        self.tasks.append(
            task
        )

        return task



    def dispatch(
        self,
        task_id: str,
    ):

        for task in self.tasks:

            if task.id == task_id:

                task.status = "RUNNING"

                return task


        raise ValueError(
            "Task not found"
        )



    def complete(
        self,
        task_id: str,
    ):

        for task in self.tasks:

            if task.id == task_id:

                task.status = "COMPLETED"

                return task


        raise ValueError(
            "Task not found"
        )
