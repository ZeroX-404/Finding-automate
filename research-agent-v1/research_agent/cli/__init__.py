from __future__ import annotations

from pathlib import Path

from research_agent.runtime import RuntimeWorkspace


PROJECT_ROOT = Path(__file__).resolve().parents[2]


DEFAULT_RUNTIME = RuntimeWorkspace(
    root=(
        PROJECT_ROOT / ".research-agent"
    ).resolve()
)


__all__ = [
    "DEFAULT_RUNTIME",
]
