from __future__ import annotations

from abc import ABC, abstractmethod


class AgentResult:

    def __init__(
        self,
        agent_name: str,
        status: str,
        output: dict | None = None,
    ):
        self.agent_name = agent_name
        self.status = status
        self.output = output or {}


class BaseAgent(ABC):

    name: str = "base"

    @abstractmethod
    def execute(self, context: dict) -> AgentResult:
        pass
