from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RuntimeConfig:

    max_iterations: int = 3

    max_retry: int = 2

    enable_researcher: bool = True

    enable_critic: bool = True

    runtime_version: str = "4.2"


    @classmethod
    def from_dict(
        cls,
        data: dict,
    ):

        return cls(
            max_iterations=data.get(
                "max_iterations",
                3,
            ),

            max_retry=data.get(
                "max_retry",
                2,
            ),

            enable_researcher=data.get(
                "enable_researcher",
                True,
            ),

            enable_critic=data.get(
                "enable_critic",
                True,
            ),

            runtime_version=data.get(
                "runtime_version",
                "4.2",
            ),
        )
