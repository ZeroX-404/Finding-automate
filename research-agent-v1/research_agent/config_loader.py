from __future__ import annotations


from .runtime_config import RuntimeConfig



def load_config(
    payload: dict | None = None,
):

    payload = payload or {}

    return RuntimeConfig.from_dict(
        payload
    )
