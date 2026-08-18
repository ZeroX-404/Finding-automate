from __future__ import annotations

from enum import StrEnum
from pathlib import Path

import yaml
from pydantic import BaseModel, Field, PrivateAttr


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
    repository_base: str = "."
    repository_roots: list[str] = Field(default_factory=list)
    capabilities: dict[str, Decision]
    _policy_dir: Path = PrivateAttr(default_factory=Path.cwd)

    @classmethod
    def load(cls, path: str | Path) -> "ScopePolicy":
        policy_path = Path(path).resolve(strict=True)
        policy = cls.model_validate(yaml.safe_load(policy_path.read_text()))
        policy._policy_dir = policy_path.parent
        return policy

    def decision(self, capability: Capability) -> Decision:
        return self.capabilities.get(capability.value, Decision.DENY)

    def require(self, capability: Capability) -> None:
        decision = self.decision(capability)
        if decision != Decision.ALLOW:
            raise PermissionError(f"{capability.value} is {decision} by scope policy.")

    def authorized_repository_roots(self) -> list[Path]:
        base = Path(self.repository_base)
        if not base.is_absolute():
            base = (self._policy_dir / base).resolve()
        else:
            base = base.resolve()

        roots: list[Path] = []
        for configured in self.repository_roots:
            raw = Path(configured)
            root = raw.resolve() if raw.is_absolute() else (base / raw).resolve()
            roots.append(root)
        return roots

    def require_repository(self, repo_root: str | Path) -> Path:
        candidate = Path(repo_root).resolve(strict=True)
        for allowed in self.authorized_repository_roots():
            try:
                candidate.relative_to(allowed)
                return candidate
            except ValueError:
                continue
        raise PermissionError(
            f"repository root {candidate} is outside configured repository_roots"
        )
