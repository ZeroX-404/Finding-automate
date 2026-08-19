from __future__ import annotations

from pathlib import Path


class RuntimeWorkspace:
    """Project-anchored directory for ephemeral research-agent state.

    The workspace is intentionally separate from source-controlled files so DBs,
    transient model artifacts, and runtime logs do not drift with the shell CWD.
    """

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root).resolve()

    def ensure(self) -> Path:
        self.root.mkdir(parents=True, exist_ok=True)
        return self.root

    def path(self, name: str) -> Path:
        if not name or name in {".", ".."}:
            raise ValueError("runtime artifact name must be non-empty")
        candidate = Path(name)
        if candidate.is_absolute() or ".." in candidate.parts:
            raise ValueError("runtime artifact name must stay inside workspace")
        return self.ensure() / candidate

    def db(self, name: str) -> Path:
        filename = name if name.endswith(".db") else f"{name}.db"
        return self.path(filename)
