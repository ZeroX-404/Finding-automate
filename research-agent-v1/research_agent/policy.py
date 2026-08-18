from __future__ import annotations

from enum import StrEnum
from pathlib import Path

import yaml
from pydantic import BaseModel, Field


class Decision(StrEnum):
    ALLOW = "ALLOW"
    DENY = "DENY"
    ASK = "ASK"


class Capability(StrEnum):
    REASON = "reason"
    REPO_READ = "repo:read"
    STATIC_SCAN = "scanner:static"
    SANDBOX_EXECUTE = "sandbox:execute"
    NETWORK_READ = "network:read"
    TARGET_TEST = "target:test"
    REPO_WRITE = "repo:write"
    GIT_COMMIT = "git:commit"
    EXTERNAL_SUBMIT = "external:submit"


class ScopePolicy(BaseModel):
    scope_id: str
    repository_roots: list[str] = Field(default_factory=list)
    capabilities: dict[str, Decision]

    @classmethod
    def load(cls, path: str | Path) -> "ScopePolicy":
        return cls.model_validate(yaml.safe_load(Path(path).read_text()))

    def decision(self, capability: Capability) -> Decision:
        return self.capabilities.get(capability.value, Decision.DENY)

    def require(self, capability: Capability) -> None:
        decision = self.decision(capability)
        if decision != Decision.ALLOW:
            raise PermissionError(f"{capability.value} is {decision} by scope policy.")
