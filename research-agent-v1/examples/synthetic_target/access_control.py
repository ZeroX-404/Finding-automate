"""Intentionally vulnerable local fixture used only by the V1 acceptance test."""


def read_profile(current_user: str, requested_user: str, profiles: dict[str, str]) -> str:
    """Return a requested profile without checking that the requester owns it."""
    return profiles[requested_user]
